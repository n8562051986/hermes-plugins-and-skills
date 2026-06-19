"""cai-chat plugin: /cai <question> — AI chat via Command Code Web UI (http://127.0.0.1:5000).

Works in CLI and gateway (Telegram, Discord, etc.).
Forwards queries to the running commandcode-webui Flask app and reads SSE responses.
- Manages conversation ID for context carry-over
- Saves chat history to ~/.hermes/cai-history/ for reference

Requires the web UI to be running (python app.py in commandcode-webui/).
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WEBUI_BASE = 'http://127.0.0.1:5000'
MAX_OUTPUT_CHARS = 50_000
TIMEOUT = 300  # 5 min

HISTORY_DIR = Path.home() / '.hermes' / 'cai-history'

DEFAULT_MODEL = 'deepseek/deepseek-v4-flash'


def _session_file() -> Path:
    """File that stores the current conversation id."""
    return Path.home() / '.hermes' / 'cai-session.json'


def _load_session() -> Optional[str]:
    """Load saved conversation id."""
    sf = _session_file()
    if sf.exists():
        try:
            data = json.loads(sf.read_text())
            return data.get('conv_id')
        except Exception:
            pass
    return None


def _save_session(conv_id: str):
    """Save conversation id for subsequent calls."""
    sf = _session_file()
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps({'conv_id': conv_id, 'ts': time.time()}))


def _clear_session():
    """Reset conversation (start fresh)."""
    sf = _session_file()
    if sf.exists():
        sf.unlink()


def _save_history(role: str, content: str, model: str):
    """Append a message to today's history file."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    date_str = time.strftime('%Y-%m-%d')
    hf = HISTORY_DIR / f'{date_str}.jsonl'

    entry = json.dumps({
        'role': role,
        'content': content,
        'model': model,
        'ts': time.time(),
    })
    with open(hf, 'a') as f:
        f.write(entry + '\n')


def _new_conversation() -> Optional[str]:
    """Create a new conversation via the web UI API."""
    try:
        req = urllib.request.Request(
            f'{WEBUI_BASE}/api/new',
            method='POST',
            data=b'{}\n',
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get('conv_id')
    except Exception:
        return None


def _chat_request(query: str, conv_id: str, model: str) -> Optional[str]:
    """Send a chat request to the web UI and collect the full response."""
    body = json.dumps({'q': query, 'conv_id': conv_id, 'm': model}).encode()
    req = urllib.request.Request(
        f'{WEBUI_BASE}/api/chat',
        method='POST',
        data=body,
        headers={'Content-Type': 'application/json'},
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            full_text = []
            for line_bytes in resp:
                line = line_bytes.decode().strip()
                if line.startswith('data: '):
                    payload = json.loads(line[6:])
                    if 'text' in payload:
                        full_text.append(payload['text'])
                    elif 'error' in payload:
                        return f"Error: {payload['error']}"
                    elif payload.get('done'):
                        break
            return ''.join(full_text).strip() or None
    except urllib.error.HTTPError as e:
        return f"Error (HTTP {e.code}): {e.reason}"
    except urllib.error.URLError:
        return (
            "Web UI tidak merespon. Jalankan dulu:\n"
            "  cd ~/clawd/commandcode-webui && python app.py\n"
            "atau pastikan http://127.0.0.1:5000 sudah jalan."
        )
    except Exception as e:
        return f"Error: {e}"


def _handle_cai(raw_args: str) -> Optional[str]:
    query = raw_args.strip()

    # Parse special commands
    if query == '/new':
        _clear_session()
        return 'Session reset. Percakapan baru dimulai.'
    if query == '/help':
        return (
            "/cai <question> — tanya AI via Command Code Web UI\n"
            "/cai /new — mulai percakapan baru (reset konteks)\n"
            "/cai /help — bantuan ini"
        )

    if not query:
        return (
            "Usage: /cai <question>\n"
            "       /cai /new  — reset session\n"
            "       /cai /help — bantuan\n"
            "Example: /cai apa itu python"
        )

    # Load or create conversation
    conv_id = _load_session()
    if not conv_id:
        conv_id = _new_conversation()
        if not conv_id:
            return (
                "Gagal membuat percakapan baru. Pastikan web UI jalan:\n"
                "  cd ~/clawd/commandcode-webui && python app.py"
            )
        _save_session(conv_id)

    model = DEFAULT_MODEL

    # Send query
    _save_history('user', query, model)
    output = _chat_request(query, conv_id, model)

    if output is None:
        return "Web UI returned empty response."

    if output.startswith('Error'):
        return output

    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n... [output truncated]"

    _save_history('assistant', output, model)

    # Footer
    today = time.strftime('%Y-%m-%d')
    footer = f"\n\n──  📁 {HISTORY_DIR}/{today}.jsonl"
    return output + footer


def register(ctx) -> None:
    """Register the /cai slash command."""
    ctx.register_command(
        "cai",
        handler=_handle_cai,
        description="AI chat via Command Code Web UI (http://127.0.0.1:5000) — pakai web interface",
        args_hint="<question>",
    )
    logger.info(
        "cai-chat loaded. Web UI: %s, Model: %s, History: %s",
        WEBUI_BASE, DEFAULT_MODEL, HISTORY_DIR,
    )
