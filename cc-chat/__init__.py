"""cc-chat plugin: /cc <question> — AI chat via Command Code CLI (cmd -p).

Works in CLI and gateway (Telegram, Discord, etc.).
Calls `cmd -p` in headless mode to answer using your Command Code subscription.
- Uses --continue for conversational context between calls
- Saves chat history to ~/.hermes/cc-history/ for reference

Requires `cmd` to be logged in (run `cmd login` first).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MAX_OUTPUT_CHARS = 50_000
TIMEOUT = 300  # 5 min
MAX_TURNS = 50  # conversation turns (--continue accumulates across calls)

HISTORY_DIR = Path.home() / '.hermes' / 'cc-history'

DEFAULT_MODEL = 'deepseek/deepseek-v4-flash'


def _session_file() -> Path:
    """File that stores the current cmd session id for context carry-over."""
    return Path.home() / '.hermes' / 'cc-session.json'


def _load_session() -> Optional[str]:
    """Load saved cmd session id."""
    sf = _session_file()
    if sf.exists():
        try:
            data = json.loads(sf.read_text())
            return data.get('session_id')
        except Exception:
            pass
    return None


def _save_session(session_id: str):
    """Save cmd session id for subsequent calls."""
    sf = _session_file()
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps({'session_id': session_id, 'ts': time.time()}))


def _clear_session():
    """Reset session (start fresh)."""
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


def _handle_cc(raw_args: str) -> Optional[str]:
    query = raw_args.strip()

    # Parse special commands
    if query == '/new':
        _clear_session()
        return 'Session reset. Percakapan baru dimulai.'
    if query == '/help':
        return (
            "/cc <question> — tanya AI via Command Code\n"
            "/cc /new — mulai percakapan baru (reset konteks)\n"
            "/cc /help — bantuan ini"
        )

    if not query:
        return (
            "Usage: /cc <question>\n"
            "       /cc /new  — reset session\n"
            "       /cc /help — bantuan\n"
            "Example: /cc refactor auth module"
        )

    try:
        session_id = _load_session()
        model = DEFAULT_MODEL

        # Build args
        args = ['cmd', '-p', '-m', model, '--skip-onboarding', f'--max-turns={MAX_TURNS}']

        if session_id:
            # Resume existing session
            args += ['--resume', session_id, query]
        else:
            # First call — use --verbose to capture session id, or --continue as fallback
            args += ['--verbose', query]

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )

        output = (result.stdout or '').strip()
        stderr = (result.stderr or '').strip()

        # Save history
        _save_history('user', query, model)
        if output:
            _save_history('assistant', output, model)

        # Extract session ID from stderr if this was the first call
        if not session_id and stderr:
            # Format from cmd --verbose: "session: <uuid>" on stderr
            for part in stderr.split():
                part_clean = part.strip().rstrip('.')
                if len(part_clean) == 36 and part_clean.count('-') == 4:
                    _save_session(part_clean)
                    break
            else:
                # Couldn't find session id, but we'll use --continue next time
                # which automatically picks the latest session
                pass

        if result.returncode != 0:
            if result.returncode == 3:
                return (
                    "Command Code belum login. Jalankan:\n"
                    "  cmd login\n"
                    "di terminal, lalu coba lagi."
                )
            return f"Error (exit {result.returncode}): {stderr or 'command failed'}"

        if not output:
            return "Command Code returned empty response."

        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n... [output truncated]"

        # Add a footer with file path reference (useful for TUI)
        today = time.strftime('%Y-%m-%d')
        footer = f"\n\n──  📁 {HISTORY_DIR}/{today}.jsonl"
        return output + footer

    except subprocess.TimeoutExpired:
        return f"Command Code query timed out after {TIMEOUT}s."
    except FileNotFoundError:
        return "cmd CLI not found. Install: npm i -g command-code@latest"
    except Exception as e:
        return f"Error: {e}"


def register(ctx) -> None:
    """Register the /cc slash command."""
    ctx.register_command(
        "cc",
        handler=_handle_cc,
        description="AI chat via Command Code (cmd -p) — pakai subscription, ada konteks & history",
        args_hint="<question>",
    )
    logger.info(
        "cc-chat loaded. Model: %s, Max turns: %d, History: %s",
        DEFAULT_MODEL, MAX_TURNS, HISTORY_DIR,
    )
