# 消息类型模块设计文档

**日期**: 2026-06-13  
**版本**: 0.1.0  
**文件**: `micro_agent/messages.py`

---

## 背景

`minimal_agent.py` 中的消息是原始 dict 混用：`{"role": "user", "content": ...}`。随着 agent 能力增长，需要：

- 显式区分"模型回答"和"工具调用"（当前 tool_calls 嵌在 assistant 消息里）
- 为上下文压缩预留 `ContextSummary` 类型
- 提供类型安全的消息列表操作

参考 MiniCode 的 `types.ts` 中的 8 种 `ChatMessage`，选 6 种起步。

---

## 设计决策

### 选型：dataclass

用 Python `dataclass` 而非 Pydantic，因为：
- 零外部依赖
- 足够轻量（每种类型只有 2-4 个字段）
- 类型检查靠 `isinstance()`，运行时 zero-cost

### 6 种消息类型（方案 B）

| 类型 | 用途 | 关键字段 |
|------|------|---------|
| `SystemMessage` | 系统提示词 | `content: str` |
| `UserMessage` | 用户输入 | `content: str` |
| `AssistantMessage` | 模型最终文本回答 | `content: str` |
| `AssistantToolCall` | 一次工具调用 | `tool_use_id`, `tool_name`, `input` |
| `ToolResult` | 工具执行结果 | `tool_use_id`, `content`, `is_error` |
| `ContextSummary` | 上下文压缩摘要 | `content`, `compressed_count`, `timestamp` |

### 序列化

两个方向都需要：
1. **内部 → OpenAI 线格式**（`to_openai_format`）—— 发送给 DeepSeek API
2. **OpenAI 响应 → 内部**（`from_openai_response`）—— 解析 API 返回的 tool_calls

---

## 和现有代码的关系

| 现有 `minimal_agent.py` | 新 `messages.py` |
|--------------------------|-----------------|
| `msgs.append({"role":"user",...})` | `msgs.append(UserMessage(...))` |
| `msg.tool_calls` 嵌入 assistant 消息 | 拆成独立 `AssistantToolCall` 列表 |
| `{"role":"tool",...}` | `ToolResult(...)` |
| 无上下文压缩 | `ContextSummary` |

agent loop 不再直接拼 dict，而是用 `to_openai_format(msgs)` 转换。

---

## 测试结果

```
输入: System + User + AssistantToolCall + ToolResult + AssistantMessage
输出: 5 条 OpenAI 兼容消息
  ✅ role: system
  ✅ role: user  
  ✅ role: assistant (含 tool_calls)
  ✅ role: tool
  ✅ role: assistant (最终答案)
```

全部通过。下一步：ToolRegistry。
