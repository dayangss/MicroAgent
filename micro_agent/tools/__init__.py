# micro_agent/tools/__init__.py
"""MicroAgent builtin tools — aligned with MiniCode tools/index.ts."""

from ..tool_registry import ToolDefinition, ToolRegistry
from ..skills import discover_skills
from .web_search import web_search
from .web_fetch import web_fetch
from .list_files import list_files
from .read_file import read_file
from .write_file import write_file
from .edit_file import edit_file
from .grep_files import grep_files
from .ask_user import ask_user
from .load_skill import _create_load_skill_tool


def create_registry(cwd: str) -> ToolRegistry:
    skills = discover_skills(cwd)
    load_skill_fn = _create_load_skill_tool(cwd)

    reg = ToolRegistry(skills=skills)
    reg.register_many([
        ToolDefinition("web_search", "Search the public web using DuckDuckGo.",
            web_search, {"properties": {"query": {"type": "string"}}, "required": ["query"]}),
        ToolDefinition("web_fetch", "Fetch a web page and extract readable text.",
            web_fetch, {"properties": {"url": {"type": "string"}}, "required": ["url"]}),
        ToolDefinition("list_files", "List files and directories relative to workspace. Up to 200.",
            list_files, {"properties": {"path": {"type": "string"}}, "required": []}),
        ToolDefinition("read_file", "Read a UTF-8 text file. Use offset+limit for large files.",
            read_file, {"properties": {"path": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}}, "required": ["path"]}),
        ToolDefinition("write_file", "Write a UTF-8 text file to disk.",
            write_file, {"properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}),
        ToolDefinition("edit_file", "Edit a file by exact text replacement. search must match once.",
            edit_file, {"properties": {"path": {"type": "string"}, "search": {"type": "string"}, "replace": {"type": "string"}}, "required": ["path", "search", "replace"]}),
        ToolDefinition("grep_files", "Search for text in files using ripgrep.",
            grep_files, {"properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}),
        ToolDefinition("ask_user", "Ask the user a question and wait for reply.",
            ask_user, {"properties": {"question": {"type": "string"}}, "required": ["question"]}),
        ToolDefinition("load_skill", "Load the full contents of a named SKILL.md so you can follow that workflow accurately.",
            load_skill_fn, {"properties": {"name": {"type": "string"}}, "required": ["name"]}),
    ])
    return reg
