# micro_agent/tools/__init__.py
"""MicroAgent builtin tools — registered to ToolRegistry."""

from ..tool_registry import ToolDefinition, ToolRegistry
from .search import web_search
from .wiki import get_wiki_summary
from .web import fetch_page
from .calculator import calculator
from .file_ops import read_file, write_file, list_directory
from .code_exec import execute_python, execute_shell


def create_registry():
    reg = ToolRegistry()
    reg.register_many([
        ToolDefinition("web_search", "Search Wikipedia+DuckDuckGo.",
            web_search, {"properties": {"query": {"type": "string"}}, "required": ["query"]}),
        ToolDefinition("get_wiki_summary", "Fetch Wikipedia summary by pageid/title.",
            get_wiki_summary, {"properties": {"pageid_or_title": {"type": "string"}, "sentences": {"type": "integer"}}, "required": ["pageid_or_title"]}),
        ToolDefinition("fetch_page", "Fetch text from a URL.",
            fetch_page, {"properties": {"url": {"type": "string"}}, "required": ["url"]}),
        ToolDefinition("calculator", "Evaluate math: +-*/(), sqrt, pi.",
            calculator, {"properties": {"expression": {"type": "string"}}, "required": ["expression"]}),
        ToolDefinition("read_file", "Read file from disk.",
            read_file, {"properties": {"path": {"type": "string"}}, "required": ["path"]}),
        ToolDefinition("write_file", "Write content to a file. Creates parent dirs.",
            write_file, {"properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}),
        ToolDefinition("list_directory", "List files at path. Default '.'.",
            list_directory, {"properties": {"path": {"type": "string"}}, "required": []}),
        ToolDefinition("execute_python", "Run Python code in subprocess (10s timeout).",
            execute_python, {"properties": {"code": {"type": "string"}}, "required": ["code"]}),
        ToolDefinition("execute_shell", "Run shell command (10s, blocked: rm,sudo,mkfs).",
            execute_shell, {"properties": {"command": {"type": "string"}}, "required": ["command"]}),
    ])
    return reg
