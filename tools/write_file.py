# micro_agent/tools/write_file.py
"""write_file — 写文件到磁盘。"""

import os


def write_file(path: str, content: str) -> str:
    try:
        dirname = os.path.dirname(path) or "."
        os.makedirs(dirname, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} bytes to {path}."
    except Exception as e:
        return f"Write error: {e}"
