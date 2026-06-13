# 工具文件拆分 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `main.py` 中的 9 个工具函数拆到 `micro_agent/tools/` 独立文件，对齐 MiniCode 的 `src/tools/` 结构。

**Architecture:** 每个工具一个文件，`tools/__init__.py` 提供 `create_registry()` 工厂函数。`main.py` 从 `from .tools import create_registry` 引用，不再定义工具函数。

**Tech Stack:** Python 3.10+, dataclasses, 不引入新依赖。

---

### Task 1: 创建 `tools/` 包骨架

**Files:**
- Create: `micro_agent/tools/__init__.py`

- [ ] **Step 1: 创建 tools 包入口文件**

```python
# micro_agent/tools/__init__.py
"""MicroAgent 内置工具——注册到 ToolRegistry。"""

from ..tools import ToolDefinition, ToolRegistry

from .search import web_search
from .wiki import get_wiki_summary
from .web import fetch_page
from .calculator import calculator
from .file_ops import read_file, write_file, list_directory
from .code_exec import execute_python, execute_shell


def create_registry() -> ToolRegistry:
    """注册所有内置工具，返回 ToolRegistry。"""
    reg = ToolRegistry()
    reg.register_many([
        ToolDefinition("web_search",       "Search Wikipedia+DuckDuckGo.",
            web_search, {"properties":{"query":{"type":"string"}},"required":["query"]}),
        ToolDefinition("get_wiki_summary", "Fetch Wikipedia summary by pageid/title.",
            get_wiki_summary, {"properties":{"pageid_or_title":{"type":"string"},"sentences":{"type":"integer"}},"required":["pageid_or_title"]}),
        ToolDefinition("fetch_page",       "Fetch text from a URL.",
            fetch_page, {"properties":{"url":{"type":"string"}},"required":["url"]}),
        ToolDefinition("calculator",       "Evaluate math: +-*/(), sqrt, pi.",
            calculator, {"properties":{"expression":{"type":"string"}},"required":["expression"]}),
        ToolDefinition("read_file",        "Read file from disk.",
            read_file, {"properties":{"path":{"type":"string"}},"required":["path"]}),
        ToolDefinition("write_file",       "Write content to a file.",
            write_file, {"properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}),
        ToolDefinition("list_directory",   "List files at path.",
            list_directory, {"properties":{"path":{"type":"string"}},"required":[]}),
        ToolDefinition("execute_python",   "Run Python code (10s timeout).",
            execute_python, {"properties":{"code":{"type":"string"}},"required":["code"]}),
        ToolDefinition("execute_shell",    "Run shell command (10s).",
            execute_shell, {"properties":{"command":{"type":"string"}},"required":["command"]}),
    ])
    return reg
```

- [ ] **Step 2: 验证 import**

```bash
python3 -c "from micro_agent.tools import create_registry; create_registry()"
```
Expected: ImportError（还没有创建子文件，但 import 语法正确）

---

### Task 2: 提取 `search.py`

**Files:**
- Create: `micro_agent/tools/search.py`
- Modify: `micro_agent/main.py`（删除 `_web_search`）

- [ ] **Step 1: 写 search 工具文件**

```python
# micro_agent/tools/search.py
"""web_search — Wikipedia API + DuckDuckGo 搜索。"""

import re
import requests

UA = {"User-Agent": "MicroAgent/0.1.0"}


def web_search(query: str) -> str:
    parts = []
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php",
            params={"action":"query","list":"search","srsearch":query,
                    "format":"json","srlimit":3,"origin":"*"},
            headers=UA, timeout=10)
        for i, p in enumerate(r.json().get("query",{}).get("search",[])[:3]):
            s = re.sub(r"<[^>]+>", "", p["snippet"])
            parts.append(f"[{i+1}] {p['title']} (pageid:{p['pageid']})\n    {s[:250]}")
    except: pass
    try:
        r2 = requests.get("https://api.duckduckgo.com/",
            params={"q":query,"format":"json","no_html":1,"skip_disambig":1}, timeout=10)
        a = r2.json().get("Abstract","")
        if a: parts.append(f"[DDG] {a[:400]}")
    except: pass
    return "\n\n".join(parts) or f"No results for '{query}'."
```

- [ ] **Step 2: 从 main.py 删除 `_web_search`**

删除 `main.py` 中的 `_web_search` 函数（行 25-42）。保留 `import re`（其他函数可能用到）。

- [ ] **Step 3: 验证**

```bash
python3 -c "
from dotenv import load_dotenv; import os,sys
_d = os.path.dirname(os.path.abspath('micro_agent/main.py'))
load_dotenv(os.path.join(os.path.dirname(_d), 'agent_project', '.env'))
sys.path.insert(0,'.')
from micro_agent.tools import create_registry
r = create_registry()
assert 'web_search' in r.list_names()
print('OK: web_search registered')
"
```
Expected: `OK: web_search registered`

---

### Task 3: 提取 `wiki.py` + `web.py`

**Files:**
- Create: `micro_agent/tools/wiki.py`
- Create: `micro_agent/tools/web.py`
- Modify: `micro_agent/main.py`（删除 `_get_wiki`、`_fetch_page`）

- [ ] **Step 1: 写 wiki 文件**

```python
# micro_agent/tools/wiki.py
"""get_wiki_summary — Wikipedia REST API 摘要。"""

import requests

UA = {"User-Agent": "MicroAgent/0.1.0"}


def get_wiki_summary(pageid_or_title: str, sentences: int = 5) -> str:
    try:
        pid = int(pageid_or_title)
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{pid}",
            headers=UA, timeout=10)
    except ValueError:
        r = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/",
            params={"title":pageid_or_title}, headers=UA, timeout=10)
    if r.status_code == 404: return f"Page not found: {pageid_or_title}"
    r.raise_for_status()
    d = r.json()
    s = ". ".join(d.get("extract","").split(". ")[:sentences])
    url = d.get("content_urls",{}).get("desktop",{}).get("page","")
    return f"{s}.\n- {url}" if url else s
```

- [ ] **Step 2: 写 web（fetch_page）文件**

```python
# micro_agent/tools/web.py
"""fetch_page — 抓取网页全文。"""

import re
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "MicroAgent/0.1.0"}


def fetch_page(url: str) -> str:
    try:
        r = requests.get(url, timeout=10, headers=UA); r.raise_for_status()
        soup = BeautifulSoup(r.text,"html.parser")
        for t in soup(["script","style","nav","footer","header"]): t.decompose()
        text = re.sub(r"\n\s*\n","\n\n", soup.get_text(separator="\n")).strip()
        return text[:3000] if len(text)>3000 else text
    except Exception as e: return f"Fetch error: {e}"
```

- [ ] **Step 3: 从 main.py 删除对应函数**

删除 `_get_wiki`（行 44-57）和 `_fetch_page`（行 59-66）。

- [ ] **Step 4: 验证**

```bash
python3 -c "from micro_agent.tools import create_registry; r=create_registry(); assert 'get_wiki_summary' in r.list_names(); assert 'fetch_page' in r.list_names(); print('OK')"
```

---

### Task 4: 提取 `calculator.py` + `file_ops.py`

**Files:**
- Create: `micro_agent/tools/calculator.py`
- Create: `micro_agent/tools/file_ops.py`
- Modify: `micro_agent/main.py`（删除 `_calculator`、`_read_file`、`_write_file`、`_list_dir`）

- [ ] **Step 1: 写 calculator 文件**

```python
# micro_agent/tools/calculator.py
"""calculator — 安全数学求值。"""

import math


def calculator(expression: str) -> str:
    if not all(c in set("0123456789+-*/.() e") for c in expression):
        return "Error: math ops only."
    try:
        return str(eval(expression, {"__builtins__": {}},
                        {"sqrt": math.sqrt, "pi": math.pi}))
    except Exception as e:
        return f"Error: {e}"
```

- [ ] **Step 2: 写文件操作文件**

```python
# micro_agent/tools/file_ops.py
"""read_file / write_file / list_directory — 文件系统操作。"""

import os


def read_file(path: str) -> str:
    try:
        with open(path) as f: return f.read()
    except FileNotFoundError: return f"'{path}' not found."
    except Exception as e: return f"Read error: {e}"


def write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path,"w") as f: f.write(content)
        return f"Wrote {len(content)} bytes to {path}."
    except Exception as e: return f"Write error: {e}"


def list_directory(path: str = ".") -> str:
    try:
        items = sorted(os.listdir(path))
        return "\n".join(items) or "(empty)"
    except Exception as e: return f"List error: {e}"
```

- [ ] **Step 3: 从 main.py 删除对应函数**

删除 `_calculator`、`_read_file`、`_write_file`、`_list_dir`。

- [ ] **Step 4: 验证**

```bash
python3 -c "from micro_agent.tools import create_registry; r=create_registry(); assert 'calculator' in r.list_names(); assert 'read_file' in r.list_names(); assert 'write_file' in r.list_names(); assert 'list_directory' in r.list_names(); print('OK')"
```

---

### Task 5: 提取 `code_exec.py`

**Files:**
- Create: `micro_agent/tools/code_exec.py`
- Modify: `micro_agent/main.py`（删除 `_execute_python`、`_execute_shell`）

- [ ] **Step 1: 写代码执行工具文件**

```python
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
```

- [ ] **Step 2: 从 main.py 删除对应函数**

删除 `_execute_python`（行 93-105）和 `_execute_shell`（行 107-114）。

- [ ] **Step 3: 验证全部工具**

```bash
python3 -c "
from dotenv import load_dotenv; import os,sys
_d = os.path.dirname(os.path.abspath('micro_agent/main.py'))
load_dotenv(os.path.join(os.path.dirname(_d), 'agent_project', '.env'))
sys.path.insert(0,'.')
from micro_agent.main import create_agent
from micro_agent.agent_loop import run

client, reg, sp = create_agent()
print(f'Tools: {reg.list_names()}')

# Test all 9 tools registered
assert len(reg) == 9
print('OK: all 9 tools registered')

# E2E test
answer, _ = run('Calculate 2**8', registry=reg, client=client, system_prompt=sp)
print(f'Answer: {answer[:100]}')
"
```

- [ ] **Step 4: 清理 main.py 不再需要的 import**

从 main.py 顶部删除：`json`、`math`、`re`（如果只被拆出的文件用）、`subprocess`、`tempfile`

- [ ] **Step 5: 去掉 main.py 中的 `create_registry`，改为 import**

在 main.py 中：
```python
# 删除: def create_registry() -> ToolRegistry: ...
# 改为: from .tools import create_registry
```

---

### Task 6: 提交

- [ ] **Step 1: Git add & commit**

```bash
git add -A
git status
git commit -m "refactor: split tools into micro_agent/tools/ package

extract 9 tool functions from main.py into 6 files:
- tools/search.py   : web_search
- tools/wiki.py     : get_wiki_summary
- tools/web.py      : fetch_page
- tools/calculator.py: calculator
- tools/file_ops.py : read_file, write_file, list_directory
- tools/code_exec.py: execute_python, execute_shell

tools/__init__.py provides create_registry() factory.
main.py ~190 → ~75 lines."
```
