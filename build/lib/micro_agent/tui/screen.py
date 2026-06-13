# micro_agent/tui/screen.py
"""TUI screen — multi-line input, markdown rendering, streaming output.

Uses prompt_toolkit for rich terminal interaction.
"""

import sys, os
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from .input_parser import parse_command, get_command_help, COMMANDS

os.makedirs(os.path.expanduser("~/.micro_agent"), exist_ok=True)
HISTORY_FILE = os.path.expanduser("~/.micro_agent/history")


STYLE = Style.from_dict({
    "prompt": "#00aa00 bold",
    "separator": "#888888",
    "tool-output": "#8888ff",
    "error": "#ff4444",
    "answer": "#ffffff",
    "thinking": "#aaaa00 italic",
})

agent_completer = WordCompleter(list(COMMANDS.keys()), ignore_case=True, sentence=True)


def create_session() -> PromptSession:
    kb = KeyBindings()

    @kb.add("c-d")
    def _(event):
        """Ctrl+D exits."""
        event.app.exit()

    return PromptSession(
        history=FileHistory(HISTORY_FILE),
        key_bindings=kb,
        completer=agent_completer,
        style=STYLE,
        message=[("class:prompt", "µ> ")],
        multiline=False,
    )


def print_agent_header(workspace: str, tools_count: int, tool_names: list[str]):
    print(f"\nMicroAgent v0.2")
    print(f"Workspace: {workspace}")
    print(f"Tools ({tools_count}): {', '.join(tool_names[:8])}")
    if len(tool_names) > 8:
        print(f"  ... and {len(tool_names) - 8} more")
    print("/help for commands | Ctrl+D to exit\n")


def print_tool_step(step: int, tool_name: str, args: str, status: str):
    marker = "✓" if status == "OK" else "✗"
    color = "" if status == "OK" else "\033[31m"
    reset = "" if status == "OK" else "\033[0m"
    print(f"  [{step}] {tool_name}({args}) → {color}{marker}{reset}")
