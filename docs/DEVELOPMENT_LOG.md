# MicroAgent 开发历程与现状报告

**项目**: MicroAgent (micro-agent)  
**仓库**: <https://github.com/dayangss/MicroAgent>  
**日期**: 2026-06-13  
**版本**: v0.2.0  
**总代码量**: ~1027 行 Python（含 tools/compact/tui 子模块）

---

## 一、对话时间线

### 阶段 0：从零搭建 Agent Loop（Stage 1）

- 创建 `minimal_agent.py`，用 DeepSeek API 实现最小 agent 循环
- 支持 function calling（tool use）：search、calculator、read_file
- 加入最大步数限制、超时、错误处理
- 产出：132 行 → 最终精简到 211 行的可运行 agent

### 阶段 1：真实工具接入（Stage 2.1）

- 把假的 search 替换为 Wikipedia API + DuckDuckGo
- 新增 `get_wikipedia_summary`、`fetch_page` 工具
- 加入循环检测（连续 3 次相同调用 → 注入提示）
- 工具从 3 个扩展到 5 个

### 阶段 2：鲁棒性加固（Stage 2.4）

- 指数退避重试（429/5xx）：等 1s → 2s → 4s
- 引用幻觉检测：提取 `[N]` 标记，验证是否超出 source 范围
- 按句子边界截断工具结果（之前硬切 2000 字符）

### 阶段 3：工具对齐 MiniCode（Stage 2.2-2.3）

- 删除通用工具（calculator、wiki、代码执行），新增 coding 专用工具
- 当前 8 工具：web_search, web_fetch, list_files, read_file, write_file, edit_file, grep_files, ask_user
- 工具名完全对齐 MiniCode 的 `src/tools/`

### 阶段 4：代码执行 + 文件工具

- 新增 `execute_python`（subprocess 执行，10s 超时）
- 新增 `execute_shell`（shell 命令执行，危险命令拦截）
- 新增 `write_file`、`list_directory`
- 9 工具阶段

### 阶段 5：工具文件拆分

- 参考 MiniCode 目录结构，拆 `main.py` 中的 9 个工具到独立文件
- 解决了 `tools.py` → `tool_registry.py` 的循环导入
- `main.py` 从 190 行缩小到 70 行

### 阶段 6：架构重构 → MicroAgent

- 重命名为 MicroAgent，"coding_agent" → "micro_agent"
- 设计 6 种消息类型 → 升级为 8 种（方案 B+）
- 消息类型：System / User / Assistant / AssistantToolCall / ToolResult / ContextSummary / AssistantProgress / SnipBoundary
- ToolRegistry 类：register / find / execute / to_openai_schema
- System Prompt 模块：独立生成（工具列表 + 行为规则 + memory）
- Memory 模块：自动发现 MINI.md / CLAUDE.md

### 阶段 7：上下文压缩引擎（Compact）

- 对齐 MiniCode 的 4 级压缩策略：
  - Tier 1: microcompact — 删除孤儿 tool_calls
  - Tier 2: auto_compact — 消息过多时生成摘要
  - Tier 3: snip_compact — 移除中间工具交互对
  - Tier 4: context_collapse — 截断过长工具结果（600 字符上限）

### 阶段 8：TUI 交互界面

- 基于 prompt_toolkit 的终端 UI
- 支持 /commands（/help /tools /memory /exit）
- Ctrl+D 退出，历史记录文件
- 命令补全、彩色输出

### 阶段 9：全局安装支持

- `pyproject.toml` + `setuptools` 支持 `pip install -e .`
- `_ensure_env()` 自动查找 API key：
  1. 当前目录 `.env`
  2. 向上 4 级目录
  3. `~/.micro_agent/.env`（全局配置）
- `setup.py` 支持传统安装方式

---

## 二、当前项目结构

```
micro_agent/
├── .env                    # API key 配置
├── .gitignore
├── LICENSE                 # MIT
├── README.md               # 使用文档
├── pyproject.toml          # Python 包配置
├── bin/micro-agent         # CLI 入口
├── docs/                   # 设计文档（6 份）
│   ├── 01-messages-design.md
│   ├── 02-tool-registry-design.md
│   ├── 03-agent-loop-design.md
│   ├── 04-prompt-design.md
│   ├── 05-memory-design.md
│   ├── 06-main-entry-design.md
│   └── superpowers/plans/  # 实现计划
├── micro_agent/
│   ├── __init__.py
│   ├── __main__.py          # python -m micro_agent
│   ├── messages.py          # 8 种消息类型 + OpenAI 转换 (124 行)
│   ├── tool_registry.py     # ToolRegistry + ToolDefinition (68 行)
│   ├── agent_loop.py        # Agent 主循环 (86 行)
│   ├── prompt.py            # System prompt 生成 (33 行)
│   ├── memory.py            # 指令文件发现 (108 行)
│   ├── main.py              # 简单版入口 (58 行)
│   ├── tty_app.py           # TUI 入口 (65 行)
│   ├── tools/               # 8 个工具文件
│   │   ├── __init__.py      # create_registry() 工厂
│   │   ├── web_search.py    # DuckDuckGo 搜索
│   │   ├── web_fetch.py     # 网页抓取
│   │   ├── list_files.py    # 目录列表
│   │   ├── read_file.py     # 文件读取（支持 offset/limit）
│   │   ├── write_file.py    # 文件写入
│   │   ├── edit_file.py     # 精确文本替换
│   │   ├── grep_files.py    # ripgrep 代码搜索
│   │   └── ask_user.py      # 用户交互
│   ├── compact/             # 4 级上下文压缩
│   │   ├── __init__.py
│   │   ├── microcompact.py  # Tier 1
│   │   ├── auto_compact.py  # Tier 2
│   │   ├── snip_compact.py  # Tier 3
│   │   └── context_collapse.py  # Tier 4
│   └── tui/                 # 终端 UI
│       ├── __init__.py
│       ├── input_parser.py  # /command 解析
│       └── screen.py        # prompt_toolkit 界面
│
└── (保留参考)
    ├── agent_project/minimal_agent.py  # Stage 1 产物
    ├── MiniCode/                        # MiniCode TypeScript 源码
    └── superpowers/                     # 开发方法论
```

---

## 三、与 MiniCode 的对齐状态

| MiniCode 模块 | MicroAgent 对应 | 对齐状态 |
|--------------|----------------|---------|
| `src/types.ts` (ChatMessage 8 种) | `messages.py` 8 种 | ✅ 完全对齐 |
| `src/tool.ts` (ToolRegistry) | `tool_registry.py` | ✅ 对齐 |
| `src/tools/` (12 tools) | `tools/` (8 tools) | ✅ 核心工具对齐 |
| `src/agent-loop.ts` | `agent_loop.py` | ✅ 核心循环对齐 |
| `src/compact/` (4 tiers) | `compact/` (4 tiers) | ✅ 架构对齐 |
| `src/prompt.ts` | `prompt.py` | ✅ 对齐 |
| `src/memory.ts` | `memory.py` | ✅ 对齐 |
| `src/tui/` | `tui/` | ✅ 基础对齐 |
| `src/mcp.ts` | — | ❌ 未实现 |
| `src/skills.ts` | — | ❌ 未实现 |
| `src/permissions.ts` | — | ❌ 部分（ask_user 工具可用） |
| `src/anthropic-adapter.ts` | — | ❌ 不需要（用 DeepSeek） |
| `src/history.ts` | — | ❌ 未实现 |
| `src/session.ts` | — | ❌ 未实现 |
| `src/tools/` (load-skill, modify-file, patch-file) | — | ❌ 未实现 |

---

## 四、Git 提交历史（核心里程碑）

```
df35060 fix: repair truncated memory.py + rebuild egg
bdba201 chore: remove setup.py, use pyproject.toml only
ea08d55 feat: runnable from any project + pip install support
a55be4f feat: TUI interactive shell (prompt_toolkit)
990880c feat: 4-tier context compact engine (MiniCode aligned)
deb6af8 feat: add edit_file tool + 8-type messages (scheme B+)
6317f60 refactor: align tools with MiniCode
77d7e71 refactor: split tools into micro_agent/tools/ package
4fdd5e4 init: MicroAgent v0.1.0 — Python coding agent
```

---

## 五、功能集成清单

### ✅ 已实现

- [x] Agent 核心循环（tool call 解析、执行、结果传回）
- [x] 指数退避重试（429 / 5xx）
- [x] 循环检测（连续 3 次相同调用 → 注入提示）
- [x] 引用幻觉检测
- [x] 8 种消息类型 + OpenAI 线格式转换
- [x] ToolRegistry 工具注册表
- [x] System Prompt 自动生成
- [x] Memory 系统（MINI.md / CLAUDE.md 自动发现）
- [x] 8 个 coding 工具（搜索/抓取/文件读写/编辑/grep/询问）
- [x] 4 级上下文压缩
- [x] prompt_toolkit TUI 界面
- [x] pyproject.toml + pip install 支持
- [x] 全局 API key 配置（`~/.micro_agent/.env`）
- [x] 项目级 `.env` 优先级覆盖

### ❌ 未实现（后续规划）

- [ ] MCP 协议集成
- [ ] Skills 系统
- [ ] 权限管理（除 ask_user 外）
- [ ] modify_file / patch_file 工具
- [ ] 会话历史持久化
- [ ] Streaming 输出
- [ ] 插件系统
- [ ] 测试套件

---

## 六、Windows 使用方式

```powershell
# 1. 安装
cd E:\agent_project\learn_agent\micro_agent
pip install -e .

# 2. 全局 API key（一次性）
mkdir $env:USERPROFILE\.micro_agent -Force
@"
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
"@ | Out-File $env:USERPROFILE\.micro_agent\.env -Encoding utf8

# 3. 在任何项目中使用
cd E:\any\project
python -m micro_agent          # TUI 版
python -m micro_agent.main     # 简单版

# 4. 或在代码中
python -c "from micro_agent.main import create_agent; c,r,s=create_agent(); print('OK:', len(r), 'tools')"
```

---

## 七、关键设计决策

1. **6 → 8 种消息类型**：在 MiniCode 基础上加了 `AssistantProgress` 和 `SnipBoundary`，为上下文压缩和进度反馈预留接口

2. **DeepSeek API**：选择 DeepSeek（OpenAI 兼容），成本低、token 便宜，适合学习和日常使用

3. **工具命名对齐 MiniCode**：`list_files` 而非 `list_directory`，`grep_files` 而非 `grep_code`，便于以后参考 MiniCode 的 prompt 和 tool schema

4. **pyproject.toml 作为唯一构建方式**：删除了 `setup.py`，统一用现代 Python 打包标准

5. **`package_dir={"micro_agent": "."}` 解决 pip install 路径问题**：因为项目根目录就是 `micro_agent/`，需要告诉 setuptools 当前目录就是包根

6. **API key 三级查找策略**：当前目录 → 父目录链 → 全局 `~/.micro_agent/`

---

## 八、设计文档

| 文档 | 说明 |
|------|------|
| `docs/01-messages-design.md` | 6 → 8 种消息类型选型、序列化设计 |
| `docs/02-tool-registry-design.md` | ToolDefinition + ToolRegistry 设计 |
| `docs/03-agent-loop-design.md` | agent loop 流程、循环检测、超时 |
| `docs/04-prompt-design.md` | system prompt 组装规则 |
| `docs/05-memory-design.md` | MINI.md 自动发现、去重、截断 |
| `docs/06-main-entry-design.md` | create_agent 工厂 + main 入口 |
| `docs/superpowers/plans/2026-06-13-tools-split.md` | 工具拆分实现计划 |
