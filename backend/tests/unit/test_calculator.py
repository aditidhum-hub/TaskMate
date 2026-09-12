"""Unit tests for AST-based safe Calculator Tool."""

import pytest

from backend.app.tools.calculator import calculate

# ---------------------------------------------------------------------------
# Basic Arithmetic & Precedence
# ---------------------------------------------------------------------------


def test_basic_addition():
    """Verify simple addition."""
    assert calculate("20 + 5") == 25.0


def test_basic_subtraction():
    """Verify simple subtraction."""
    assert calculate("20 - 5") == 15.0


def test_basic_multiplication():
    """Verify simple multiplication."""
    assert calculate("20 * 5") == 100.0


def test_basic_division():
    """Verify simple division."""
    assert calculate("20 / 5") == 4.0


def test_parentheses_precedence():
    """Verify parentheses override standard operator precedence."""
    assert calculate("(10 + 5) * 2") == 30.0
    assert calculate("10 + 5 * 2") == 20.0


def test_unary_operators():
    """Verify unary positive and negative operators."""
    assert calculate("-5 + 10") == 5.0
    assert calculate("+5 + 10") == 15.0
    assert calculate("-(3 * 4)") == -12.0


def test_float_arithmetic():
    """Verify floating point operations."""
    assert calculate("2.5 + 3.75") == 6.25
    assert calculate("10 / 4") == 2.5


# ---------------------------------------------------------------------------
# Power, Modulo, and Floor Division
# ---------------------------------------------------------------------------


def test_power_operator():
    """Verify exponentiation via ** and ^."""
    assert calculate("2 ** 3") == 8.0
    assert calculate("2 ^ 3") == 8.0
    assert calculate("3 ^ 2") == 9.0


def test_modulo_operator():
    """Verify modulo arithmetic."""
    assert calculate("20 % 6") == 2.0


def test_floor_division():
    """Verify floor division."""
    assert calculate("20 // 6") == 3.0


# ---------------------------------------------------------------------------
# Safe Whitelisted Functions
# ---------------------------------------------------------------------------


def test_sqrt_function():
    """Verify safe sqrt function."""
    assert calculate("sqrt(16)") == 4.0
    assert calculate("sqrt(25) + 5") == 10.0


def test_abs_function():
    """Verify safe abs function."""
    assert calculate("abs(-42)") == 42.0
    assert calculate("abs(42)") == 42.0


def test_round_function():
    """Verify safe round function with 1 or 2 arguments."""
    assert calculate("round(3.6)") == 4.0
    assert calculate("round(3.14159, 2)") == 3.14


def test_ceil_and_floor_functions():
    """Verify safe ceil and floor functions."""
    assert calculate("ceil(4.1)") == 5.0
    assert calculate("floor(4.9)") == 4.0


# ---------------------------------------------------------------------------
# Error Handling & Edge Cases
# ---------------------------------------------------------------------------


def test_division_by_zero():
    """Verify division by zero raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError, match="Division by zero is undefined"):
        calculate("20 / 0")

    with pytest.raises(ZeroDivisionError, match="Division by zero is undefined"):
        calculate("20 // 0")

    with pytest.raises(ZeroDivisionError, match="Modulo by zero is undefined"):
        calculate("20 % 0")


def test_negative_square_root():
    """Verify square root of negative number raises descriptive ValueError."""
    with pytest.raises(ValueError, match="Square root of a negative number"):
        calculate("sqrt(-4)")


def test_empty_or_whitespace_expression():
    """Verify empty expression raises ValueError."""
    with pytest.raises(ValueError, match="Expression cannot be empty"):
        calculate("")

    with pytest.raises(ValueError, match="Expression cannot be empty"):
        calculate("   ")


def test_invalid_syntax():
    """Verify malformed syntax raises descriptive ValueError."""
    with pytest.raises(ValueError, match="Invalid arithmetic syntax"):
        calculate("20 + + * 5")

    with pytest.raises(ValueError, match="Invalid arithmetic syntax"):
        calculate("(10 + 5")


# ---------------------------------------------------------------------------
# Security & Zero eval() Policy Tests (Code Injection Resistance)
# ---------------------------------------------------------------------------


def test_code_injection_import_blocked():
    """Verify __import__ payload is rejected."""
    with pytest.raises(ValueError):
        calculate("__import__('os').system('ls')")


def test_code_injection_eval_blocked():
    """Verify eval() call is rejected."""
    with pytest.raises(ValueError, match="Function 'eval' is not allowed"):
        calculate("eval('2 + 2')")


def test_code_injection_exec_blocked():
    """Verify exec() call is rejected."""
    with pytest.raises(ValueError, match="Function 'exec' is not allowed"):
        calculate("exec('x = 1')")


def test_code_injection_open_blocked():
    """Verify open() call is rejected."""
    with pytest.raises(ValueError, match="Function 'open' is not allowed"):
        calculate("open('/etc/passwd')")


def test_variable_lookup_blocked():
    """Verify variable identifiers (e.g. x, os, __builtins__) are rejected."""
    with pytest.raises(ValueError, match="Variable lookups .* are disallowed"):
        calculate("x + 5")

    with pytest.raises(ValueError, match="Variable lookups .* are disallowed"):
        calculate("__builtins__")


def test_attribute_access_blocked():
    """Verify object attribute traversal is rejected."""
    with pytest.raises(ValueError):
        calculate("(1).__class__.__bases__[0].__subclasses__()")
