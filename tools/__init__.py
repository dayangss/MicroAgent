# micro_agent/tools/__init__.py
"""MicroAgent builtin tools — aligned with MiniCode tools/index.ts."""

from ..tool_registry import ToolDefinition, ToolRegistry
from .web_search import web_search
from .web_fetch import web_fetch
from .list_files import list_files
from .read_file import read_file
from .write_file import write_file
from .grep_files import grep_files
from .ask_user import ask_user


def create_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register_many([
        ToolDefinition("web_search", "Search the public web using DuckDuckGo. For current info, docs, or anything outside the local workspace.",
            web_search, {"properties": {"query": {"type": "string"}}, "required": ["query"]}),
        ToolDefinition("web_fetch", "Fetch a web page and extract readable text. Use after web_search when you need full content of a specific page.",
            web_fetch, {"properties": {"url": {"type": "string"}}, "required": ["url"]}),
        ToolDefinition("list_files", "List files and directories relative to workspace root. Up to 200 entries.",
            list_files, {"properties": {"path": {"type": "string"}}, "required": []}),
        ToolDefinition("read_file", "Read a UTF-8 text file. Large files read in chunks via offset and limit.",
            read_file, {"properties": {"path": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}}, "required": ["path"]}),
        ToolDefinition("write_file", "Write a UTF-8 text file relative to workspace root.",
            write_file, {"properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}),
        ToolDefinition("grep_files", "Search for text in files using ripgrep. Returns file paths + line numbers + matches.",
            grep_files, {"properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}),
        ToolDefinition("ask_user", "Ask the user a clarifying question and wait for their reply.",
            ask_user, {"properties": {"question": {"type": "string"}}, "required": ["question"]}),
    ])
    return reg
