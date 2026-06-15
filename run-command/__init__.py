"""
run-command plugin: /run <shell command> — execute directly, no AI tokens.

Works in CLI and gateway (Telegram, Discord, etc.).
Simply runs the command via subprocess and returns stdout+stderr.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Max output length to avoid flooding chat (50 KB)
MAX_OUTPUT_CHARS = 50_000
# Max execution time (seconds)
CMD_TIMEOUT = 30
# Shell to use (bash on Linux/Mac, cmd on Windows)
_SHELL = "bash" if sys.platform != "win32" else "cmd.exe"
_SHELL_FLAG = "-c" if sys.platform != "win32" else "/c"


def _handle_run(raw_args: str) -> Optional[str]:
    """Execute a shell command and return its output."""
    cmd = raw_args.strip()
    if not cmd:
        return "Usage: /run <command>\nExample: /run ls -la\n         /run pwd\n         /run cd ~ && git status"

    # Safety: block dangerous commands
    blocked_prefixes = (
        "rm -rf /", "rm -rf ~", "rm -rf .", "rm -rf *",
        "sudo", "su ", "chmod 777", "chown",
        "> /dev/sda", "dd if=", "mkfs.", "fdisk", "format ",
        ":(){ :|:& };:", "forkbomb",
        "shutdown", "reboot", "poweroff", "halt",
        "wget http", "curl http", "nc -e", "bash -i >&",
    )
    cmd_lower = cmd.lower()
    for prefix in blocked_prefixes:
        if cmd_lower.startswith(prefix):
            return f"Blocked: '{prefix.strip()}' — command not allowed for safety."

    try:
        result = subprocess.run(
            [_SHELL, _SHELL_FLAG, cmd],
            capture_output=True,
            text=True,
            timeout=CMD_TIMEOUT,
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(result.stderr)

        output = "".join(output_parts).strip()

        if not output:
            if result.returncode == 0:
                return "Command completed successfully (no output)."
            else:
                return f"Command failed (exit code {result.returncode})."

        # Truncate if too long
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n... [output truncated]"

        # Wrap in code block if multiline
        if "\n" in output:
            return f"```\n{output}\n```"
        return output

    except subprocess.TimeoutExpired:
        return f"Command timed out after {CMD_TIMEOUT}s."
    except FileNotFoundError:
        return f"Shell not found: {_SHELL}"
    except Exception as e:
        return f"Error: {e}"


def register(ctx) -> None:
    """Register the /run slash command."""
    ctx.register_command(
        "run",
        handler=_handle_run,
        description="Execute a shell command directly (zero AI tokens)",
        args_hint="<command>",
    )
