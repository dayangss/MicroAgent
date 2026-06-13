# micro_agent/tui/input_parser.py
"""TUI input — parse user command line. Handle /commands and multi-line input."""

import shlex


COMMANDS = {
    "/help": "Show available commands.",
    "/memory": "Show memory files loaded.",
    "/tools": "List available tools.",
    "/exit": "Exit MicroAgent.",
    "/q": "Exit MicroAgent.",
    "/quit": "Exit MicroAgent.",
}


def parse_command(line: str) -> str | None:
    """Return command name if line starts with / and is recognized, else None."""
    if not line.startswith("/"):
        return None
    cmd = line.split()[0] if line else ""
    return cmd if cmd in COMMANDS else None


def get_command_help() -> str:
    return "\n".join(f"  {k} - {v}" for k, v in COMMANDS.items())
