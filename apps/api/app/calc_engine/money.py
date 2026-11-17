"""Money type: Decimal amount + ISO 4217 currency. Floats are rejected on purpose."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

Number = Decimal | int | str


def D(value: Number) -> Decimal:
    """Convert to Decimal. Floats are refused to avoid binary rounding errors."""
    if isinstance(value, bool):
        raise TypeError("bool is not a number")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    raise TypeError(f"unsupported numeric type {type(value).__name__}; pass Decimal, int or str")


class CurrencyMismatchError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", D(self.amount))
        if len(self.currency) != 3 or not self.currency.isalpha() or not self.currency.isupper():
            raise ValueError(f"invalid currency code: {self.currency!r}")
        if not self.amount.is_finite():
            raise ValueError("amount must be finite")

    @classmethod
    def zero(cls, currency: str) -> Money:
        return cls(Decimal(0), currency)

    def _same(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError("can only combine Money with Money")
        if other.currency != self.currency:
            raise CurrencyMismatchError(f"{self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._same(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Number) -> Money:
        return Money(self.amount * D(factor), self.currency)

    __rmul__ = __mul__

    def __truediv__(self, divisor: Number) -> Money:
        d = D(divisor)
        if d == 0:
            raise ZeroDivisionError("division of Money by zero")
        return Money(self.amount / d, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def ratio(self, other: Money) -> Decimal:
        """self / other as a plain number (same currency)."""
        self._same(other)
        if other.amount == 0:
            raise ZeroDivisionError("ratio with zero denominator")
        return self.amount / other.amount

    def rounded(self, places: int = 2) -> Decimal:
        """Rounding for DISPLAY only. Never round intermediate results."""
        return self.amount.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)

    def __str__(self) -> str:
        return f"{self.rounded()} {self.currency}"


def money_sum(items: list[Money], currency: str) -> Money:
    total = Money.zero(currency)
    for m in items:
        total = total + m
    return total
