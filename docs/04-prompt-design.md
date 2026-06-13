# Prompt 模块设计文档

**日期**: 2026-06-13
**版本**: 0.1.0
**文件**: `micro_agent/prompt.py`

---

## 背景

`minimal_agent.py` 没有独立的 system prompt —— 每次用 user 消息包住指令。MiniCode 的 `buildSystemPrompt()` 从五个来源拼装提示词：

1. 角色定义 + 行为规则
2. CWD 路径
3. 可用工具列表（动态）
4. 权限上下文
5. 记忆文件（MINI.md / CLAUDE.md）

---

## 设计

```python
def build_system_prompt(
    cwd: str,
    registry: ToolRegistry,
    memory: str = "",
) -> str:
```

- `registry` 不再只在 agent loop 里用，也传给 prompt builder 生成工具说明
- `memory` 留给后续 2.4 记忆系统，现在留空

---

## 测试结果

```
测试输入: registry 含 2 个工具 (calculator, search), cwd=/home/..., memory="User prefers Python."
输出: 997 字符, 结构清晰
  ✅ 角色定义 — 包含
  ✅ cwd 路径 — 包含
  ✅ 工具列表 (含数量) — calculator, search
  ✅ 行为规则 (<progress>/<final>) — 包含