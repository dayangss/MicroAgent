# micro_agent/tools/edit_file.py
"""edit_file — 精确文本替换编辑文件。"""

import os


def edit_file(path: str, search: str, replace: str) -> str:
    """
    search: 精确查找的字符串（必须在文件中恰好出现一次，或被 replace_all 配置）
    replace: 替换成的字符串

    Returns success message or error.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        return f"Error: '{path}' not found."
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="latin-1") as f:
                original = f.read()
        except Exception as e:
            return f"Error reading '{path}': {e}"
    except Exception as e:
        return f"Error reading '{path}': {e}"

    if search not in original:
        return f"Error: search text not found in '{path}'."

    count = original.count(search)
    if count > 1:
        return (
            f"Error: search text found {count} times in '{path}'. "
            "Use a more specific string (include more surrounding context) "
            "so it matches exactly once."
        )

    new_content = original.replace(search, replace, 1)
    try:
        dirname = os.path.dirname(path) or "."
        os.makedirs(dirname, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return f"Error writing '{path}': {e}"

    return f"Edited '{path}': replaced 1 occurrence."
