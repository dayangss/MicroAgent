# ToolRegistry 设计文档

**日期**: 2026-06-13  
**版本**: 0.1.0  
**文件**: `micro_agent/tools.py`

---

## 背景

`minimal_agent.py` 的工具管理是一个 `dict` 映射：`{"web_search": web_search, ...}`。每次新增工具要改三处：函数实现、TOOLS schema 列表、TOOL_MAP 字典。这在小规模时够了，但继续扩展需要：

- 一个地方管理工具注册、查找、执行
- 支持运行时添加/移除工具（比如后面要接 MCP）
- 统一的错误处理和安全参数校验
- 单一来源生成 OpenAI tools schema

---

## 设计

### ToolDefinition

每个工具是一个 `ToolDefinition` 对象：`{name, description, parameters, func}`。

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable
    parameters: dict  # JSON Schema properties + required
```

不是随意函数→工具，而是显式注册。

### ToolRegistry

```python
class ToolRegistry:
    def register(self, tool: ToolDefinition) -> None
    def execute(self, name: str, args: dict) -> ToolResult
    def to_openai_schema(self) -> list[dict]  # 生成发给 API 的 tools 数组
    def list_names(self) -> list[str]
```

### 和现有代码的关系

| 旧 `minimal_agent.py` | 新 `ToolRegistry` |
|----------------------|-------------------|
| `TOOLS = [...]` 硬编码列表 | `registry.to_openai_schema()` 动态生成 |
| `TOOL_MAP = {...}` 字典 | `registry._tools: dict` 内部管理 |
| `func(**args)` 直接调用 | `registry.execute(name, args)` 统一入口（含错误处理） |
| 新增工具改 3 处 | 新增工具调用一次 `registry.register()` |

### 安全改进

- `registry.execute()` 包裹 try/except，工具报错不会崩掉 agent loop
- 校验未知工具名，返回结构化错误

---

## 预期测试

```
注册 9 个工具 → to_openai_schema() → 9 条 schema
execute("unknown") → ToolResult(is_error=True)
execute("