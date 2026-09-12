"""Safe mathematical expression evaluator implementing Zero eval() Policy."""

import ast
import math
from collections.abc import Callable
from typing import Any

# Whitelisted mathematical functions safe for evaluation
SAFE_FUNCTIONS: dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "round": round,
    "abs": abs,
    "ceil": math.ceil,
    "floor": math.floor,
}

MAX_EXPRESSION_LENGTH = 500


def _evaluate_node(node: ast.AST) -> float:
    """Recursively evaluate an AST node within strict mathematical constraints.

    Disallows variable lookups, imports, attribute access, and arbitrary code execution.
    """
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    if isinstance(node, ast.UnaryOp):
        operand = _evaluate_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("Division by zero is undefined.")
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ZeroDivisionError("Division by zero is undefined.")
            return float(left // right)
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("Modulo by zero is undefined.")
            return left % right
        if isinstance(node.op, (ast.Pow, ast.BitXor)):
            if left == 0 and right < 0:
                raise ZeroDivisionError("Zero cannot be raised to a negative power.")
            try:
                res = math.pow(left, right)
                return res
            except OverflowError:
                raise ValueError("Arithmetic calculation resulted in numerical overflow.") from None

        raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise TypeError("Direct function calls only. Attribute or nested calls are disallowed.")

        func_name = node.func.id.lower()
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not allowed.")

        if node.keywords:
            raise ValueError("Keyword arguments are not supported in math functions.")

        args: list[Any] = [_evaluate_node(arg) for arg in node.args]

        if func_name == "sqrt":
            if len(args) != 1:
                raise ValueError("sqrt() takes exactly 1 argument.")
            if args[0] < 0:
                raise ValueError("Square root of a negative number is undefined for real numbers.")
            return SAFE_FUNCTIONS["sqrt"](args[0])

        if func_name == "round":
            if len(args) == 1:
                return float(SAFE_FUNCTIONS["round"](args[0]))
            if len(args) == 2:
                return float(SAFE_FUNCTIONS["round"](args[0], int(args[1])))
            raise ValueError("round() takes 1 or 2 arguments.")

        if func_name in ("abs", "ceil", "floor"):
            if len(args) != 1:
                raise ValueError(f"{func_name}() takes exactly 1 argument.")
            return float(SAFE_FUNCTIONS[func_name](args[0]))

    if isinstance(node, ast.Name):
        raise TypeError(f"Variable lookups (e.g. '{node.id}') are disallowed.")

    raise TypeError(f"Unsupported syntax construct: {type(node).__name__}")


def calculate(expression: str) -> float:
    """Safely calculate the result of an arithmetic expression without eval().

    Args:
        expression: Mathematical expression string (e.g., '20 + 5', '(10 + 5) * 2').

    Returns:
        float: Computed numerical result.

    Raises:
        ValueError: For empty expressions, invalid syntax, disallowed constructs,
                    or mathematical errors.
        ZeroDivisionError: For division or modulo by zero.
    """
    if not expression or not isinstance(expression, str):
        raise ValueError("Expression cannot be empty.")

    sanitized = expression.strip()
    if not sanitized:
        raise ValueError("Expression cannot be empty or solely whitespace.")

    if len(sanitized) > MAX_EXPRESSION_LENGTH:
        raise ValueError(f"Expression exceeds maximum allowed length of {MAX_EXPRESSION_LENGTH} characters.")

    try:
        parsed_tree = ast.parse(sanitized, mode="eval")
    except SyntaxError as err:
        raise ValueError(f"Invalid arithmetic syntax: {err.msg}") from err

    try:
        result = _evaluate_node(parsed_tree)
    except TypeError as err:
        raise ValueError(str(err)) from err

    return round(result, 10)
