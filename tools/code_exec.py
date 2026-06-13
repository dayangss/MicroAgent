# micro_agent/tools/code_exec.py
"""execute_python / execute_shell — 代码和命令执行。"""

import os
import subprocess
import tempfile


def execute_python(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code); tmp = f.name
    try:
        r = subprocess.run(["python3",tmp], capture_output=True, text=True, timeout=10)
        out, err = r.stdout.strip(), r.stderr.strip()
        if err: out = (out+"\n" if out else "") + "[stderr]\n" + err
        return out or "(no output)"
    except subprocess.TimeoutExpired: return "Timeout (10s)."
    except Exception as e: return f"Execution error: {e}"
    finally:
        try: os.unlink(tmp)
        except OSError: pass


def execute_shell(command: str) -> str:
    for d in ["rm -rf","sudo","mkfs","dd if=","format","shutdown"]:
        if d in command.lower(): return f"Blocked: '{d}'."
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return (r.stdout+r.stderr).strip() or "(no output)"
    except subprocess.TimeoutExpired: return "Timeout (10s)."
    except Exception as e: return f"Shell error: {e}"
