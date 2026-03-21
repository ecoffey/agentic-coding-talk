from __future__ import annotations

import dataclasses
import re
import typing
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal

from logpipe.parser import LogRecord

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Op = Literal["=", "!=", "<", ">", "<=", ">=", "~"]

Predicate = Callable[[LogRecord], bool]

VALID_OPS: frozenset[str] = frozenset(typing.get_args(Op))

VALID_FIELDS: frozenset[str] = frozenset(
    f.name for f in dataclasses.fields(LogRecord)
)


def _base_type(t: type) -> type:
    """Return the concrete type from T | None (Optional[T]), or T unchanged."""
    args = typing.get_args(t)
    if args:
        return next(a for a in args if a is not type(None))
    return t


# Coercion map derived from LogRecord's own type annotations.
# int | None fields (e.g. bytes) resolve to int.
_FIELD_TYPES: dict[str, type] = {
    name: _base_type(t)
    for name, t in typing.get_type_hints(LogRecord).items()
}

# ---------------------------------------------------------------------------
# Domain object
# ---------------------------------------------------------------------------


@dataclass
class FilterExpr:
    """A single comparison predicate: field op value."""
    field: str
    op: Op
    value: Any  # already coerced to field's native type


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r'"[^"]*"'      # double-quoted string
    r"|'[^']*'"     # single-quoted string
    r"|!=|<=|>="    # two-char operators (must precede single-char)
    r"|[=<>~]"      # single-char operators
    r"|\S+"         # bare words: field names, keywords, unquoted values
)


def _tokenize(expr: str) -> list[str]:
    return _TOKEN_RE.findall(expr)


# ---------------------------------------------------------------------------
# Predicate combinators
# ---------------------------------------------------------------------------

def _and(a: Predicate, b: Predicate) -> Predicate:
    return lambda r: a(r) and b(r)


def _or(a: Predicate, b: Predicate) -> Predicate:
    return lambda r: a(r) or b(r)


# ---------------------------------------------------------------------------
# Value coercion
# ---------------------------------------------------------------------------

def _coerce(field: str, token: str) -> Any:
    """Strip quotes from quoted tokens; otherwise cast to the field's type."""
    if token.startswith('"') or token.startswith("'"):
        return token[1:-1]
    cast = _FIELD_TYPES.get(field, str)
    try:
        return cast(token)
    except (ValueError, TypeError):
        return token


# ---------------------------------------------------------------------------
# Predicate builder
# ---------------------------------------------------------------------------

def _make_predicate(fe: FilterExpr) -> Predicate:
    """
    Build a callable predicate from a FilterExpr.

    Always returns a Predicate. The op is validated against VALID_OPS before
    FilterExpr is constructed, so the match below is exhaustive — the
    AssertionError branch is unreachable in correct usage.
    """
    def pred(record: LogRecord) -> bool:
        val = getattr(record, fe.field, None)
        if val is None:
            return False
        op, cmp = fe.op, fe.value
        if op == "=":   return val == cmp   # noqa: E701
        if op == "!=":  return val != cmp   # noqa: E701
        if op == "<":   return val < cmp    # noqa: E701
        if op == ">":   return val > cmp    # noqa: E701
        if op == "<=":  return val <= cmp   # noqa: E701
        if op == ">=":  return val >= cmp   # noqa: E701
        if op == "~":   return str(cmp).lower() in str(val).lower()  # noqa: E701
        raise AssertionError(f"unreachable op: {fe.op!r}")
    return pred


# ---------------------------------------------------------------------------
# Expression parser  (recursive descent, AND > OR precedence)
# ---------------------------------------------------------------------------

class _ExprParser:
    """
    Stateful recursive-descent parser for filter expressions.

    Grammar:
        expr     := and_expr ("OR" and_expr)*
        and_expr := clause ("AND" clause)*
        clause   := FIELD OP VALUE

    AND binds tighter than OR (standard boolean precedence).

    Implemented as a class so that parser state (tokens, pos) lives in
    instance variables rather than mutable-list closure hacks, and so that
    future grammar extensions (parentheses, new node types) can be added
    as additional methods.
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr
        self.tokens = _tokenize(expr.strip())
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, context: str = "token") -> str:
        if self.pos >= len(self.tokens):
            raise ValueError(
                f"Unexpected end of expression (expected {context}): {self.expr!r}"
            )
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse_clause(self) -> Predicate:
        field = self.consume("field name")
        if field.upper() in ("AND", "OR"):
            raise ValueError(
                f"Expected field name, got keyword {field!r} in: {self.expr!r}"
            )
        if field not in VALID_FIELDS:
            raise ValueError(
                f"Unknown field {field!r}. Valid fields: {sorted(VALID_FIELDS)}"
            )
        op = self.consume("operator")
        if op not in VALID_OPS:
            raise ValueError(
                f"Unknown operator {op!r}. Valid operators: {sorted(VALID_OPS)}"
            )
        value_tok = self.consume("value")
        fe = FilterExpr(field=field, op=op, value=_coerce(field, value_tok))  # type: ignore[arg-type]
        return _make_predicate(fe)

    def parse_and(self) -> Predicate:
        left = self.parse_clause()
        while self.peek() and self.peek().upper() == "AND":  # type: ignore[union-attr]
            self.consume()
            right = self.parse_clause()
            left = _and(left, right)
        return left

    def parse_or(self) -> Predicate:
        left = self.parse_and()
        while self.peek() and self.peek().upper() == "OR":  # type: ignore[union-attr]
            self.consume()
            right = self.parse_and()
            left = _or(left, right)
        return left

    def parse(self) -> Predicate:
        predicate = self.parse_or()
        if self.pos < len(self.tokens):
            raise ValueError(
                f"Unexpected token {self.tokens[self.pos]!r} in: {self.expr!r}"
            )
        return predicate


def parse_predicate(expr: str) -> Predicate:
    """Parse a filter expression string into a callable predicate."""
    return _ExprParser(expr).parse()


# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------

@dataclass
class WhereStage:
    predicate: Predicate

    def process(self, records: Iterable[LogRecord]) -> Iterable[LogRecord]:
        return (r for r in records if self.predicate(r))
