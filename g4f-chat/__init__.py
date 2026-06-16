"""g4f-chat plugin: /g4f <question> — AI chat via g4f, gratis no login.

Works in CLI and gateway (Telegram, Discord, etc.).
Calls the `ai` CLI script to answer questions via g4f (PollinationsAI).
"""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

MAX_OUTPUT_CHARS = 50_000
TIMEOUT = 120


def _handle_g4f(raw_args: str) -> Optional[str]:
    query = raw_args.strip()
    if not query:
        return (
            "Usage: /g4f <question>\n"
            "Example: /g4f apa ibukota Indonesia\n"
            "         /g4f --model gpt-4o hitung 5+7"
        )

    try:
        result = subprocess.run(
            ["ai", query],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )

        output = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode != 0:
            return f"Error: {stderr or output or f'exit code {result.returncode}'}"

        if not output:
            return "AI returned empty response."

        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n... [output truncated]"

        return output

    except subprocess.TimeoutExpired:
        return f"AI query timed out after {TIMEOUT}s."
    except FileNotFoundError:
        return "g4f AI not installed. Run: pip install g4f"
    except Exception as e:
        return f"Error: {e}"


def register(ctx) -> None:
    """Register the /g4f slash command."""
    ctx.register_command(
        "g4f",
        handler=_handle_g4f,
        description="AI chat via g4f (PollinationsAI) — gratis, no login",
        args_hint="<question>",
    )
