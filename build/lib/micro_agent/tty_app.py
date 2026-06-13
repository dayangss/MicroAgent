# micro_agent/tty_app.py
"""TUI app — entry point for interactive agent shell."""

import os, sys
from pathlib import Path

# micro_agent should be importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from micro_agent.tui.screen import (
    create_session, print_agent_header,
)
from micro_agent.tui.input_parser import parse_command, get_command_help
from micro_agent.main import create_agent
from micro_agent.agent_loop import run as run_agent


def main():
    cwd = os.getcwd()
    client, registry, system_prompt = create_agent(cwd)

    tool_names = registry.list_names()
    print_agent_header(cwd, len(registry), tool_names)

    session = create_session()

    while True:
        try:
            line = session.prompt().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not line:
            continue

        cmd = parse_command(line)
        if cmd is not None:
            if cmd in ("/exit", "/quit", "/q"):
                print("Bye.")
                break
            elif cmd == "/help":
                print(f"\nCommands:\n{get_command_help()}\n")
            elif cmd == "/tools":
                names = registry.list_names()
                print(f"\n{len(names)} tools registered:\n" + "\n".join(f"  {n}" for n in names) + "\n")
            elif cmd == "/memory":
                from micro_agent.memory import load_memory
                mem = load_memory(cwd)
                print(f"\nMemory:\n{mem}\n" if mem else "\nNo memory found.\n")
            continue

        print()
        answer, history = run_agent(
            prompt=line,
            registry=registry,
            client=client,
            system_prompt=system_prompt,
        )
        print(answer)
        print()


if __name__ == "__main__":
    main()
