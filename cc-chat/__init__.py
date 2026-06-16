"""cc-chat plugin: /cc <question> — AI chat via Command Code CLI (cmd -p).

Works in CLI and gateway (Telegram, Discord, etc.).
Calls `cmd -p` in headless mode to answer using your Command Code subscription.
Requires `cmd` to be logged in (run `cmd login` first).
"""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

MAX_OUTPUT_CHARS = 50_000
TIMEOUT = 180


def _handle_cc(raw_args: str) -> Optional[str]:
    query = raw_args.strip()
    if not query:
        return (
            "Usage: /cc <question>\n"
            "Example: /cc refactor auth module\n"
            "         /cc --plan jelaskan arsitektur ini"
        )

    try:
        result = subprocess.run(
            ["cmd", "-p", query],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )

        output = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

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

        return output

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
        description="AI chat via Command Code (cmd -p) — pakai subscription",
        args_hint="<question>",
    )
