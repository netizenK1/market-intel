"""What-if scenarios on top of the base calculation. Every scenario result is an ESTIMATE."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from .engine import calculate
from .models import Basis, CalcInput, CalcResult, CostKind
from .money import D


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    price_factor: Decimal = Decimal(1)
    sell_through: Decimal | None = None  # absolute share; None = keep input value
    freight_factor: Decimal = Decimal(1)  # applied to amount-based main freight lines


DEFAULT_SCENARIOS: tuple[Scenario, ...] = (
    Scenario("pessimistic", price_factor=D("0.9"), sell_through=D("0.6"), freight_factor=D("1.2")),
    Scenario("base"),
    Scenario("optimistic", price_factor=D("1.1"), sell_through=D("1"), freight_factor=D("0.9")),
)


def apply_scenario(inp: CalcInput, s: Scenario) -> CalcInput:
    lines = tuple(
        replace(cl, amount=cl.amount * s.freight_factor)
        if cl.kind is CostKind.MAIN_FREIGHT and cl.basis is not Basis.PERCENT_OF_GOODS and cl.amount is not None
        else cl
        for cl in inp.cost_lines
    )
    return replace(
        inp,
        sale_price=inp.sale_price * s.price_factor,
        sell_through=inp.sell_through if s.sell_through is None else s.sell_through,
        cost_lines=lines,
    )


def run_scenarios(inp: CalcInput, scenarios: tuple[Scenario, ...] = DEFAULT_SCENARIOS) -> dict[str, CalcResult]:
    return {s.name: calculate(apply_scenario(inp, s)) for s in scenarios}
