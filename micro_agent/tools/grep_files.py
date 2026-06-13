# micro_agent/tools/grep_files.py
"""grep_files — 用 ripgrep 搜索文件内容。"""

import subprocess


def grep_files(pattern: str, path: str = ".") -> str:
    try:
        r = subprocess.run(
            ["rg", "-n", "--no-heading", "--max-count=5", pattern, path],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip() or "(no matches)"
    except FileNotFoundError:
        # fallback to grep
        try:
            r = subprocess.run(
                ["grep", "-rn", "--max-count=5", pattern, path],
                capture_output=True, text=True, timeout=10
            )
            return r.stdout.strip() or "(no matches)"
        except FileNotFoundError:
            return "grep_files: ripgrep or grep not found. Install ripgrep: apt install ripgrep"
        except Exception as e:
            return f"grep_files error: {e}"
    except Exception as e:
        return f"grep_files error: {e}"
