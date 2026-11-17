"""Currency conversion. Rates are supplied by the caller (with source and date) — never fetched here."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .money import D, Money, Number


class MissingFxRateError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class FxRate:
    """1 `base` = `rate` `quote`."""

    base: str
    quote: str
    rate: Decimal
    rate_date: date
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "rate", D(self.rate))
        if self.rate <= 0:
            raise ValueError("FX rate must be positive")
        if self.base == self.quote:
            raise ValueError("base and quote must differ")


class FxTable:
    def __init__(self, rates: Iterable[FxRate] = ()) -> None:
        self._rates: dict[tuple[str, str], FxRate] = {}
        for r in rates:
            self._rates[(r.base, r.quote)] = r
        self._used: dict[tuple[str, str], FxRate] = {}

    def rate(self, base: str, quote: str) -> Decimal:
        if base == quote:
            return Decimal(1)
        direct = self._rates.get((base, quote))
        if direct is not None:
            self._used[(direct.base, direct.quote)] = direct
            return direct.rate
        inverse = self._rates.get((quote, base))
        if inverse is not None:
            self._used[(inverse.base, inverse.quote)] = inverse
            return Decimal(1) / inverse.rate
        raise MissingFxRateError(f"no FX rate for {base}->{quote}")

    def convert(self, money: Money, to_currency: str) -> Money:
        return Money(money.amount * self.rate(money.currency, to_currency), to_currency)

    def used_rates(self) -> list[FxRate]:
        """Rates actually used in a calculation — stored with the result for traceability."""
        return list(self._used.values())

    def reset_usage(self) -> None:
        self._used.clear()


def fx(base: str, quote: str, rate: Number, rate_date: date, source: str) -> FxRate:
    return FxRate(base, quote, D(rate), rate_date, source)
