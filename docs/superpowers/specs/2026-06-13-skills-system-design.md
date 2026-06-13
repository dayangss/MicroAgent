# Skills System Design — MicroAgent

**日期**: 2026-06-13
**版本**: v0.3.0 规划
**对齐目标**: MiniCode `src/skills.ts` + `src/tools/load-skill.ts`

---

## 一、目标

为 MicroAgent 添加技能（Skills）系统，让 agent 能根据上下文自动发现并加载 SKILL.md 文件，遵循其中定义的开发工作流（如 brainstorming、writing-plans、TDD 等）。

完全对齐 MiniCode 的 skills 架构模式。

---

## 二、Skills 存储结构

```
~/.micro_agent/skills/<name>/SKILL.md    # 用户级（优先）
.cwd/.mini-code/skills/<name>/SKILL.md   # 项目级
.cwd/.claude/skills/<name>/SKILL.md      # 兼容项目级
~/.claude/skills/<name>/SKILL.md         # 兼容用户级
```

去重规则：按以上优先级顺序，同名 skill 优先采用最先发现的。

`extractDescription()` 逻辑：读取 SKILL.md 中第一个非标题段落的第一行非标题文本，去除反引号。

---

## 三、新增/改造组件

### 3.1 新建 `skills.py` — 技能发现与加载

对应 MiniCode: `src/skills.ts`

```
discover_skills(cwd: str) -> List[SkillSummary]
load_skill(cwd: str, name: str) -> LoadedSkill | None
install_skill(cwd, source_path, name?, scope?) -> {name, target_path}
remove_skill(cwd, name, scope?) -> {removed, target_path}
```

数据类型：

```python
@dataclass
class SkillSummary:
    name: str
    description: str
    path: str
    source: str  # 'project' | 'user' | 'compat_project' | 'compat_user'

@dataclass
class LoadedSkill(SkillSummary):
    content: str
```

### 3.2 新建 `tools/load_skill.py` — load_skill 工具

对应 MiniCode: `src/tools/load-skill.ts`

- 工具名: `load_skill`
- 参数: `name` (string, required)
- 行为: 调用 `load_skill(cwd, name)`，返回完整 SKILL.md 内容
- 未找到时返回错误

### 3.3 改造 `tool_registry.py` — 添加元数据支持

对应 MiniCode: `src/tool.ts` metadataStore

- `ToolRegistry` 构造函数新增可选 `metadata: dict` 参数
- 新增 `get_skills() -> List[SkillSummary]` 方法
- 新增 `add_tools(tools)` 方法（未来 MCP 也需要）
- 保持向后兼容

### 3.4 改造 `tools/__init__.py` — 启动时发现技能

对应 MiniCode: `src/tools/index.ts` `createDefaultToolRegistry()`

- `create_registry(cwd: str)` 改为接受 cwd 参数
- 内部调用 `discover_skills(cwd)` 发现技能
- 将 skills 传入 ToolRegistry 元数据
- 注册 load_skill 工具

### 3.5 改造 `prompt.py` — System Prompt 添加技能列表

对应 MiniCode: `src/prompt.ts`

- `build_system_prompt()` 新增可选参数 `skills: List[SkillSummary]`
- 有技能时：逐行列出 `- <name>: <description>`
- 无技能时：显示 `- none discovered`
- 添加规则: "If the user names a skill or clearly asks for a workflow that matches a listed skill, call load_skill before following it."

### 3.6 改造 `main.py` — 传递技能数据

- `create_agent()` 传递 cwd 给 `create_registry(cwd)`
- 从 registry 获取 skills，传给 `build_system_prompt()`
- `tty_app.py` 同步更新

### 3.7 CLI `/skills` 命令

对应 MiniCode: `src/cli-commands.ts`

- TUI 中 `/skills` 列出已发现的技能（name + description + source）
- `main.py` 简单版中打印 `N skills discovered`

---

## 四、数据流

```
应用启动
  ↓
create_registry(cwd)
  ├── discover_skills(cwd)
  │     ├── 扫描 ~/.micro_agent/skills/*/SKILL.md
  │     ├── 扫描 .cwd/.mini-code/skills/*/SKILL.md
  │     ├── 扫描 .cwd/.claude/skills/*/SKILL.md
  │     └── 扫描 ~/.claude/skills/*/SKILL.md
  ├── 去重（按优先级）
  ├── ToolRegistry(metadata={skills: [...]})
  └── 注册 load_skill 工具
  ↓
build_system_prompt(cwd, registry, memory, skills=registry.get_skills())
  ↓
System Prompt 包含:
  "Available skills:
   - brainstorming: Use before creative work...
   - test-driven-development: RED-GREEN-REFACTOR..."
  ↓
用户: "用 TDD 写一个函数"
  ↓
AI 看到 skills 列表，调用 load_skill("test-driven-development")
  ↓
返回 SKILL.md 完整内容
  ↓
AI 遵循 TDD 技能指南执行
```

---

## 五、文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| Create | `micro_agent/skills.py` | 技能发现、加载、安装、删除 |
| Create | `micro_agent/tools/load_skill.py` | load_skill 工具 |
| Modify | `micro_agent/tool_registry.py` | 添加 metadata + get_skills() |
| Modify | `micro_agent/tools/__init__.py` | create_registry(cwd) + skills 发现 |
| Modify | `micro_agent/prompt.py` | skills 参数 + 技能列表输出 |
| Modify | `micro_agent/main.py` | 传递 cwd/skills |
| Modify | `micro_agent/tty_app.py` | 同步更新 |
| Modify | `micro_agent/tui/input_parser.py` | 添加 /skills 命令 |

---

## 六、非功能需求

- **零新依赖**: 仅使用 Python 标准库
- **向后兼容**: 无 skills 目录时静默降级（`- none discovered`）
- **与 MiniCode 行为一致**: 目录结构、去重规则、描述提取逻辑完全相同
- **文件 I/O 安全**: 所有文件操作有 try/except 保护
