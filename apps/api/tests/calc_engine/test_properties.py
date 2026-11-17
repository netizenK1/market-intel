"""Property-based tests: invariants that must hold for any valid input."""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from app.calc_engine import Incoterm, calculate

from .fixtures import case1_leather_bags_de, eur, usd

money_amounts = st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100000"), places=2)
rates = st.decimals(min_value=Decimal("0"), max_value=Decimal("0.5"), places=3)


@settings(max_examples=60, deadline=None)
@given(unit=money_amounts, qty=st.integers(min_value=1, max_value=100_000), price=money_amounts)
def test_landed_cost_never_below_goods_value(unit: Decimal, qty: int, price: Decimal) -> None:
    res = calculate(case1_leather_bags_de(unit_goods_value=usd(str(unit)), quantity=qty, sale_price=eur(str(price))))
    assert res.totals.total_landed_cost.amount >= res.totals.goods_value.amount


@settings(max_examples=60, deadline=None)
@given(unit=money_amounts, qty=st.integers(min_value=1, max_value=10_000))
def test_unregistered_importer_pays_exactly_the_vat_more(unit: Decimal, qty: int) -> None:
    reg = calculate(case1_leather_bags_de(unit_goods_value=usd(str(unit)), quantity=qty))
    unreg = calculate(
        case1_leather_bags_de(unit_goods_value=usd(str(unit)), quantity=qty, importer_vat_registered=False)
    )
    vat = reg.line("import_vat")
    assert vat is not None
    diff = unreg.totals.total_landed_cost.amount - reg.totals.total_landed_cost.amount
    assert abs(diff - vat.amount.amount) < Decimal("1e-18")


@settings(max_examples=60, deadline=None)
@given(rate=rates)
def test_profit_identity_holds(rate: Decimal) -> None:
    t = calculate(case1_leather_bags_de(marketplace_fee_rate=rate)).totals
    lhs = t.net_profit.amount
    rhs = t.revenue.amount - t.cogs.amount - t.variable_selling_costs.amount - t.fixed_costs.amount
    assert abs(lhs - rhs) < Decimal("1e-18")


@settings(max_examples=30, deadline=None)
@given(term=st.sampled_from(list(Incoterm)))
def test_every_incoterm_calculates_without_error(term: Incoterm) -> None:
    res = calculate(case1_leather_bags_de(incoterm=term))
    assert res.totals.unit_landed_cost.amount > 0
