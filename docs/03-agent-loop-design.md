# Agent Loop 设计文档

**日期**: 2026-06-13
**版本**: 0.1.0
**文件**: `micro_agent/agent_loop.py`

---

## 背景

`minimal_agent.py` 的 `run()` 函数在一个 for 循环里混合了：LLM 调用、tool 解析、工具执行、结果传回。现在有了 `messages.py` 和 `ToolRegistry`，可以把 agent loop 抽成独立模块。

---

## 设计对比：旧 vs 新

| 关注点 | 旧 run() | 新 agent_loop.run() |
|--------|---------|-------------------|
| 消息存储 | 原始 dict | `List[ChatMessage]` 类型安全 |
| 工具管理 | TOOL_MAP dict | `ToolRegistry` |
| 工具执行 | `func(**args)` 内联 | `registry.execute(name, args)` |
| 消息注入 | 直接 `msgs.append(dict)` | `UserMessage(...)` |
| 返回值 | 纯文本 `str` | 文本 + 消息历史列表 |
| 上下文压缩 | 无 | 接口预留（max_tokens 阈值 + 注入 ContextSummary） |

---

## 核心流程

```
用户 prompt
  │
  ▼
1. 构造 messages: [SystemMessage, UserMessage(prompt)]
  │
  ▼
2. call_llm(messages) → 内部消息列表
  │
  ├── 模型回答 → return (答案, 消息历史)
  │
  └── tool_calls →
        │
        ▼
      3. 每个 tool 调 registry.execute(name, args)
         → 得到 ToolResult
         → 追加到消息历史
         │
         ▼
      4. 检查循环检测 + 最大步数
         │
         ▼
      5. 回到步骤 2
```

---

## 接口

```python
def run(
    prompt: str,
    registry: ToolRegistry,
    system_prompt: str = "",
    max_steps: int = 12,
    timeout: float = 120.0,
) -> tuple[str, list[ChatMessage]]:
    """返回 (最终答案, 完整消息历史)"""
```

返回消息历史给调用方，调用方可以持久化或做后续摘要。

---

## 测试结果

```
测试 1: 单工具调用
  输入: "What is 15*7+3? Use the calculator."
  Step 1: calculator({"expression": "15 * 7 + 3"}) → ✓
  答案: "The result of 15 × 7 + 3 is **108**."
  消息: 5 条 (system → user → tool_call → tool_result → assistant)

测试 2: 多工具并行调用
  输入: "Search for 'python language', then calculate 100/3."
  Step 1: search({"query": "python language"}) → ✓    (并行)
  Step 1: calculator({"expression": "100/3"}) → ✓      (并行)
  答案: 两个结果汇总，正确
  消息: 7 条

✅ 消息类型、ToolRegistry、agent loop 三个模块协同正常
✅ 并行 tool calls 正确