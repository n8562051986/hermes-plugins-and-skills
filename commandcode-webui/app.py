"""Command Code Web UI — Flask backend.

Usage:
  pip install flask
  python app.py

Then open http://127.0.0.1:5000
"""

import json
import subprocess
import re
import sys
import uuid
import os
import time
from pathlib import Path
from flask import Flask, request, Response, send_file

app = Flask(__name__)

# ── Paths ───────────────────────────────────────────────────────────
HISTORY_DIR = Path(__file__).parent / 'history'
HISTORY_DIR.mkdir(exist_ok=True)

# ANSI escape regex — strips color codes, CPR, DSR, OSC, etc.
_ANSI_STRIP = re.compile(
    r'\x1b\[[0-9;]*[a-zA-Z]'       # CSI sequences
    r'|\x1b\].*?\x07'              # OSC sequences
    r'|\x1b[PX^_].*?\x1b\\'        # DCS/SOS/PM/APC
)


def strip_ansi(text: str) -> str:
    return _ANSI_STRIP.sub('', text)


# ── Models ──────────────────────────────────────────────────────────
KNOWN_MODELS = [
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-pro",
    "moonshotai/Kimi-K2.5",
    "moonshotai/Kimi-K2.6",
    "claude-sonnet-4-6",
    "claude-opus-4-7",
    "claude-haiku-4-5-20251001",
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.4-mini",
    "zai-org/GLM-5.1",
    "google/gemini-3.5-flash",
    "Qwen/Qwen3.7-Max",
    "Qwen/Qwen3.6-Plus",
]

MAX_TURNS = 50
TIMEOUT = 300  # 5 min

# In-memory: conv_id -> cmd_session_id
_sessions: dict[str, str] = {}


# ── Save / load chat history ───────────────────────────────────────

def _history_path(conv_id: str) -> Path:
    return HISTORY_DIR / f'{conv_id}.json'


def _load_history(conv_id: str) -> list:
    p = _history_path(conv_id)
    if p.exists():
        return json.loads(p.read_text())
    return []


def _save_message(conv_id: str, role: str, content: str, model: str):
    history = _load_history(conv_id)
    history.append({
        'role': role,
        'content': content,
        'model': model,
        'ts': time.time(),
    })
    _history_path(conv_id).write_text(json.dumps(history, indent=2))


# ── Routes ──────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_file('index.html')


@app.route('/api/models')
def list_models():
    return {"models": KNOWN_MODELS, "default": "deepseek/deepseek-v4-flash"}


@app.route('/api/history/<conv_id>')
def get_history(conv_id):
    """Return saved chat history for a conversation."""
    return {"messages": _load_history(conv_id)}


@app.route('/api/conversations')
def list_conversations():
    """List all saved conversations (newest first)."""
    files = sorted(HISTORY_DIR.glob('*.json'), key=os.path.getmtime, reverse=True)
    convs = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            if data:
                first = data[0]
                last = data[-1]
                convs.append({
                    'id': f.stem,
                    'title': first.get('content', '')[:60],
                    'count': len(data),
                    'updated': last.get('ts', 0),
                    'model': last.get('model', ''),
                })
        except Exception:
            pass
    return {"conversations": convs}


@app.route('/api/conversation/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    """Delete a conversation history file."""
    p = _history_path(conv_id)
    if p.exists():
        p.unlink()
    # Also remove from in-memory session map
    _sessions.pop(conv_id, None)
    return {"ok": True}


@app.route('/api/chat', methods=['POST'])
def chat():
    """Streaming chat — POST with JSON {q, m, conv_id}.

    - First msg in a conversation: runs cmd -p --verbose to capture session ID
    - Subsequent msgs: uses --resume <id> to continue
    - Responses saved to history/<conv_id>.json
    """
    data = request.get_json(silent=True) or {}
    query = (data.get('q') or '').strip()
    model = (data.get('m') or 'deepseek/deepseek-v4-flash').strip()
    conv_id = (data.get('conv_id') or '').strip()

    if not query:
        return {"error": "query required"}, 400
    if not conv_id:
        return {"error": "conv_id required"}, 400

    # Load existing history for context (for display / /cc reading)
    history = _load_history(conv_id)
    is_first = len(history) == 0

    def generate():
        full_response = ''
        cmd_session_id = _sessions.get(conv_id)

        try:
            # Build args
            args = ['cmd', '-p', '-m', model, f'--max-turns={MAX_TURNS}']

            if cmd_session_id:
                # Resume existing cmd session
                args += ['--resume', cmd_session_id, query]
            elif not is_first:
                # Have history but no saved cmd session — resume latest
                args += ['--continue', query]
            else:
                # First message — capture session ID from stderr
                args += ['--verbose', query]

            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Read stdout line by line
            for line in iter(proc.stdout.readline, ''):
                cleaned = strip_ansi(line)
                if cleaned:
                    full_response += cleaned
                    yield f"data: {json.dumps({'text': cleaned})}\n\n"

            proc.stdout.close()
            proc.wait(timeout=5)

            # Read stderr — may contain session ID or errors
            stderr_raw = proc.stderr.read()
            stderr = strip_ansi(stderr_raw)

            if proc.returncode != 0:
                if proc.returncode == 3:
                    yield f"data: {json.dumps({'error': 'Not logged in. Run: cmd login'})}\n\n"
                else:
                    reason = stderr or f'exit code {proc.returncode}'
                    yield f"data: {json.dumps({'error': reason})}\n\n"
                full_response = ''
            else:
                # Try to extract cmd session ID from stderr (from --verbose)
                # Format: "session: <uuid>" on stderr
                if not cmd_session_id and stderr:
                    for part in stderr.split():
                        part_clean = part.strip().rstrip('.')
                        if len(part_clean) == 36 and part_clean.count('-') == 4:
                            cmd_session_id = part_clean
                            _sessions[conv_id] = cmd_session_id
                            break

                # Save to history file
                if full_response.strip():
                    _save_message(conv_id, 'user', query, model)
                    _save_message(conv_id, 'assistant', full_response.strip(), model)

            yield f"data: {json.dumps({'done': True})}\n\n"

        except FileNotFoundError:
            yield f"data: {json.dumps({'error': 'cmd CLI not found. Install: npm i -g command-code@latest'})}\n\n"
        except subprocess.TimeoutExpired:
            yield f"data: {json.dumps({'error': f'Timed out after {TIMEOUT}s'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/new', methods=['POST'])
def new_conversation():
    """Start a new conversation."""
    conv_id = uuid.uuid4().hex[:12]
    return {"conv_id": conv_id}


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"  →  http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)
