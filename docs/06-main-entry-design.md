# Main 入口设计文档

**日期**: 2026-06-13
**版本**: 0.1.0
**文件**: `micro_agent/main.py`

---

## 背景

四个模块已完成：
- `messages.py` — 6 种消息类型 + OpenAI 序列化
- `tools.py` — ToolRegistry + ToolDefinition
- `agent_loop.py` — agent 主循环
- `prompt.py` — system prompt 生成
- `memory.py` — 指令文件发现加载

现在需要一个入口把它们的依赖注入串起来。

---

## 设计

```python
def create_agent(workspace: str) -> tuple[OpenAI, ToolRegistry, str]:
    """一次性创建：API 客户端 + 注册所有工具 + 生成 system prompt。"""
```

代理 `minimal_agent.py` 的 9 个工具到新的 ToolRegistry 上。

### main() 函数

```python
def main():
    # 1. 加载 .env
    # 2. 创建客户端
    # 3. 注册工具
    # 4. 加载 memory
    # 5. 生成 system prompt
    # 6. 交互循环: 读输入 → run() → 打印答案
```


---

## 测试结果

```
input: "Run Python: print(sum(range(1,101))). And list directory."

Step 1: execute_python → ok
Step 1: list_directory → ok  (parallel)

answer: 5050 + directory listing
messages: 7 total (system -> user -> assistant_tool_calls -> tool_results -> assistant)
```
