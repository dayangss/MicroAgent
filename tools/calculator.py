# micro_agent/tools/calculator.py
"""calculator — 安全数学求值。"""

import math


def calculator(expression: str) -> str:
    if not all(c in set("0123456789+-*/.() e") for c in expression):
        return "Error: math ops only."
    try:
        return str(eval(expression, {"__builtins__": {}},
                        {"sqrt": math.sqrt, "pi": math.pi}))
    except Exception as e:
        return f"Error: {e}"
