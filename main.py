#!/usr/bin/env python3
"""micro_agent/main.py — MicroAgent entry point.

Wires: messages → tools → prompt → memory → agent_loop → interactive shell.
"""

import os, sys, json, math, re, subprocess, tempfile
from openai import OpenAI
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

from .messages import ChatMessage
from .tools import ToolDefinition, ToolRegistry
from .agent_loop import run as run_agent
from .prompt import build_system_prompt
from .memory import load_memory


UA = {"User-Agent": "MicroAgent/0.1.0"}

def _web_search(query: str) -> str:
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

def _get_wiki(pageid_or_title: str, sentences: int = 5) -> str:
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

def _fetch_page(url: str) -> str:
    try:
        r = requests.get(url, timeout=10, headers=UA); r.raise_for_status()
        soup = BeautifulSoup(r.text,"html.parser")
        for t in soup(["script","style","nav","footer","header"]): t.decompose()
        text = re.sub(r"\n\s*\n","\n\n", soup.get_text(separator="\n")).strip()
        return text[:3000] if len(text)>3000 else text
    except Exception as e: return f"Fetch error: {e}"

def _calculator(expression: str) -> str:
    if not all(c in set("0123456789+-*/.() e") for c in expression):
        return "Error: math ops only."
    try: return str(eval(expression,{"__builtins__":{}},{"sqrt":math.sqrt,"pi":math.pi}))
    except Exception as e: return f"Error: {e}"

def _read_file(path: str) -> str:
    try:
        with open(path) as f: return f.read()
    except FileNotFoundError: return f"'{path}' not found."
    except Exception as e: return f"Read error: {e}"

def _write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path,"w") as f: f.write(content)
        return f"Wrote {len(content)} bytes to {path}."
    except Exception as e: return f"Write error: {e}"

def _list_dir(path: str = ".") -> str:
    try:
        items = sorted(os.listdir(path))
        return "\n".join(items) or "(empty)"
    except Exception as e: return f"List error: {e}"

def _execute_python(code: str) -> str:
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

def _execute_shell(command: str) -> str:
    for d in ["rm -rf","sudo","mkfs","dd if=","format","shutdown"]:
        if d in command.lower(): return f"Blocked: '{d}'."
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return (r.stdout+r.stderr).strip() or "(no output)"
    except subprocess.TimeoutExpired: return "Timeout (10s)."
    except Exception as e: return f"Shell error: {e}"


def create_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register_many([
        ToolDefinition("web_search",       "Search Wikipedia+DuckDuckGo.",
            _web_search, {"properties":{"query":{"type":"string"}},"required":["query"]}),
        ToolDefinition("get_wiki_summary", "Fetch Wikipedia summary by pageid/title.",
            _get_wiki, {"properties":{"pageid_or_title":{"type":"string"},"sentences":{"type":"integer"}},"required":["pageid_or_title"]}),
        ToolDefinition("fetch_page",       "Fetch text from a URL.",
            _fetch_page, {"properties":{"url":{"type":"string"}},"required":["url"]}),
        ToolDefinition("calculator",       "Evaluate math: +-*/(), sqrt, pi.",
            _calculator, {"properties":{"expression":{"type":"string"}},"required":["expression"]}),
        ToolDefinition("read_file",        "Read file from disk.",
            _read_file, {"properties":{"path":{"type":"string"}},"required":["path"]}),
        ToolDefinition("write_file",       "Write content to a file.",
            _write_file, {"properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}),
        ToolDefinition("list_directory",   "List files at path.",
            _list_dir, {"properties":{"path":{"type":"string"}},"required":[]}),
        ToolDefinition("execute_python",   "Run Python code (10s timeout).",
            _execute_python, {"properties":{"code":{"type":"string"}},"required":["code"]}),
        ToolDefinition("execute_shell",    "Run shell command (10s).",
            _execute_shell, {"properties":{"command":{"type":"string"}},"required":["command"]}),
    ])
    return reg


def _ensure_env():
    _d = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(os.path.dirname(_d), "agent_project", ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)


def create_agent(workspace: str | None = None):
    _ensure_env()
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set. Check agent_project/.env")
    cwd = workspace or os.getcwd()
    client = OpenAI(
        api_key=key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    registry = create_registry()
    memory = load_memory(cwd)
    system_prompt = build_system_prompt(cwd, registry, memory)
    return client, registry, system_prompt


def main():
    cwd = os.getcwd()
    client, registry, system_prompt = create_agent(cwd)
    print(f"MicroAgent v0.1.0")
    print(f"Workspace: {cwd}")
    print(f"Tools: {len(registry)} ({', '.join(registry.list_names())})")
    print()
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "/q"):
            print("Bye.")
            break
        answer, history = run_agent(
            prompt=user_input,
            registry=registry,
            client=client,
            system_prompt=system_prompt,
        )
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
