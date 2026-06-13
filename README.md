# MicroAgent

A lightweight terminal coding assistant built in Python. Interactive TUI with prompt_toolkit, DeepSeek-powered agent loop, and 8 tools for reading, writing, searching, and editing files.

## Quick Start

```bash
pip install -e /path/to/micro_agent
export DEEPSEEK_API_KEY=sk-your-key
cd /your/project
micro-agent
```

Or run without install:
```bash
cd /path/to/micro_agent
python -m micro_agent
```

## Tools

| Tool | Description |
|------|-------------|
| web_search | DuckDuckGo web search |
| web_fetch | Fetch page content |
| list_files | List directory entries |
| read_file | Read file with offset/limit |
| write_file | Write file to disk |
| edit_file | Exact text search-and-replace |
| grep_files | Ripgrep code search |
| ask_user | Ask user for input |

## Commands

- `/help` — Show commands
- `/tools` — List available tools
- `/memory` — Show loaded memory files
- `/exit` or Ctrl+D — Quit

## Configuration

MicroAgent searches for API keys in this order:

1. `.env` in current working directory
2. `.env` in parent directories (up to 4 levels)
3. `~/.micro_agent/.env` — **recommended for global setup**

### Global API key (all projects, set once)

**Windows (PowerShell):**
```powershell
mkdir $env:USERPROFILE\.micro_agent -Force
@"
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
"@ | Out-File -FilePath $env:USERPROFILE\.micro_agent\.env -Encoding utf8
```

**macOS / Linux:**
```bash
mkdir -p ~/.micro_agent
cat > ~/.micro_agent/.env << 'EOF'
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
EOF
```

### Per-project key

Create a `.env` file in the project root with the same format. Project `.env` takes priority over global `~/.micro_agent/.env`. Get a key from [DeepSeek Platform](https://platform.deepseek.com/api_keys).

## Architecture

Inspired by [MiniCode](https://github.com/LiuMengxuan04/MiniCode), implemented in Python with:
- 8 message types (system/user/assistant/tool_call/tool_result/context_summary/progress/snip_boundary)
- ToolRegistry with 8 built-in tools
- 4-tier context compact engine
- prompt_toolkit TUI shell
