from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from app.calc_engine import (
    Basis,
    CalcInputError,
    CostKind,
    CostLine,
    D,
    FxTable,
    Incoterm,
    MissingFxRateError,
    Money,
    Party,
    Segment,
    UnsupportedCountryError,
    calculate,
    fx,
    get_rule_pack,
    payer,
    run_scenarios,
)
from app.calc_engine.money import CurrencyMismatchError

from .fixtures import AS_OF, case1_leather_bags_de, eur, usd

# ---------------------------------------------------------------- money


def test_money_rejects_float_and_bad_currency() -> None:
    with pytest.raises(TypeError):
        Money(0.1, "EUR")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        Money(D("1"), "eur")
    with pytest.raises(TypeError):
        D(True)  # type: ignore[arg-type]


def test_money_arithmetic_and_rounding() -> None:
    assert (eur("0.1") + eur("0.2")).amount == D("0.3")
    assert (eur("10") - eur("2.5")).amount == D("7.5")
    assert (3 * eur("1.10")).amount == D("3.30")
    assert eur("2.675").rounded() == D("2.68")  # half-up, no binary float error
    assert str(eur("1.005")) == "1.01 EUR"
    assert (-eur("1")).amount == D("-1")
    with pytest.raises(CurrencyMismatchError):
        _ = eur("1") + usd("1")
    with pytest.raises(ZeroDivisionError):
        _ = eur("1") / 0
    with pytest.raises(ZeroDivisionError):
        eur("1").ratio(eur("0"))


# ---------------------------------------------------------------- fx


def test_fx_direct_inverse_identity_and_missing() -> None:
    t = FxTable([fx("EUR", "USD", "1.25", AS_OF, "fixture")])
    assert t.convert(eur("2"), "USD").amount == D("2.50")
    assert t.convert(usd("2.50"), "EUR").amount == D("2")
    assert t.convert(eur("2"), "EUR").amount == D("2")
    with pytest.raises(MissingFxRateError):
        t.convert(eur("1"), "AED")
    with pytest.raises(ValueError):
        fx("EUR", "USD", "0", AS_OF, "x")
    with pytest.raises(ValueError):
        fx("EUR", "EUR", "1", AS_OF, "x")


def test_missing_fx_rate_fails_loudly() -> None:
    with pytest.raises(MissingFxRateError):
        calculate(case1_leather_bags_de(fx=FxTable()))


# ---------------------------------------------------------------- incoterms & countries


def test_incoterm_matrix_key_cells() -> None:
    assert all(payer(Incoterm.EXW, s) is Party.BUYER for s in Segment)
    assert all(payer(Incoterm.DDP, s) is Party.SELLER for s in Segment)
    assert payer(Incoterm.FOB, Segment.MAIN_FREIGHT) is Party.BUYER
    assert payer(Incoterm.CIF, Segment.INSURANCE) is Party.SELLER
    assert payer(Incoterm.CFR, Segment.INSURANCE) is Party.BUYER
    assert payer(Incoterm.DAP, Segment.IMPORT_DUTIES_TAXES) is Party.BUYER
    assert payer(Incoterm.DAP, Segment.DEST_INLAND) is Party.SELLER


def test_unsupported_country_has_no_fallback() -> None:
    with pytest.raises(UnsupportedCountryError):
        get_rule_pack("FR")
    with pytest.raises(UnsupportedCountryError):
        calculate(case1_leather_bags_de(destination="FR"))


# ---------------------------------------------------------------- input validation


@pytest.mark.parametrize(
    "overrides",
    [
        {"quantity": 0},
        {"sell_through": D("1.5")},
        {"marketplace_fee_rate": D("1")},
        {"taxes": None},  # price_includes_vat needs a sales VAT rate
        {"unit_goods_value": eur("-1")},
    ],
)
def test_invalid_inputs_raise(overrides: dict[str, object]) -> None:
    with pytest.raises(CalcInputError):
        case1_leather_bags_de(**overrides)


def test_cost_line_validation() -> None:
    with pytest.raises(CalcInputError):
        CostLine(CostKind.INSURANCE, Basis.PERCENT_OF_GOODS, amount=eur("1"))
    with pytest.raises(CalcInputError):
        CostLine(CostKind.INSURANCE, Basis.PERCENT_OF_GOODS, rate=D("2"))
    with pytest.raises(CalcInputError):
        CostLine(CostKind.ADVERTISING, Basis.PERCENT_OF_GOODS, rate=D("0.1"))
    with pytest.raises(CalcInputError):
        CostLine(CostKind.FULFILLMENT, Basis.PER_SHIPMENT, eur("1"))
    with pytest.raises(CalcInputError):
        CostLine(CostKind.MAIN_FREIGHT, Basis.PER_SHIPMENT)
    with pytest.raises(CalcInputError):
        CostLine(CostKind.MAIN_FREIGHT, Basis.PER_SHIPMENT, eur("-5"))


# ---------------------------------------------------------------- honest incompleteness


def test_missing_freight_marks_result_incomplete() -> None:
    inp = case1_leather_bags_de()
    lines = tuple(cl for cl in inp.cost_lines if cl.kind is not CostKind.MAIN_FREIGHT)
    res = calculate(replace(inp, cost_lines=lines))
    assert not res.totals.is_complete
    assert "FREIGHT_MISSING" in res.warning_codes()


def test_missing_duty_and_vat_are_not_silently_zero() -> None:
    res = calculate(case1_leather_bags_de(duty_rates=(), hs_code=None, price_includes_vat=False, taxes=None))
    assert not res.totals.is_complete
    assert {"DUTY_RATE_MISSING", "IMPORT_VAT_MISSING", "HS_CODE_MISSING"} <= res.warning_codes()
    assert res.line("customs_duty") is None


def test_percent_insurance_and_per_unit_lines() -> None:
    inp = case1_leather_bags_de()
    lines = tuple(
        CostLine(CostKind.INSURANCE, Basis.PERCENT_OF_GOODS, rate=D("0.01")) if cl.kind is CostKind.INSURANCE else cl
        for cl in inp.cost_lines
    ) + (CostLine(CostKind.CERTIFICATION, Basis.PER_UNIT, eur("0.20")),)
    res = calculate(replace(inp, cost_lines=lines))
    assert res.line("insurance").amount.rounded() == D("69.44")  # type: ignore[union-attr]  # 1% of 6944.44
    assert res.line("certification").amount.rounded() == D("100.00")  # type: ignore[union-attr]
    assert res.totals.fixed_costs.rounded() == D("2400.00")


def test_loss_making_product_has_no_break_even() -> None:
    res = calculate(case1_leather_bags_de(sale_price=eur("20")))
    assert res.totals.break_even_units is None
    assert res.totals.net_profit.amount < 0
    assert "NO_BREAK_EVEN" in res.warning_codes()


def test_break_even_above_quantity_warns() -> None:
    res = calculate(case1_leather_bags_de(sale_price=eur("36")))
    assert res.totals.break_even_units is not None and res.totals.break_even_units > 500
    assert "BREAK_EVEN_ABOVE_QUANTITY" in res.warning_codes()


def test_non_automated_incoterm_warns() -> None:
    res = calculate(case1_leather_bags_de(incoterm=Incoterm.FCA))
    assert "INCOTERM_REVIEW" in res.warning_codes()
    assert "EXCLUDED_EXPORT_CLEARANCE" in res.warning_codes()


def test_zero_sales_has_no_margin() -> None:
    res = calculate(case1_leather_bags_de(sell_through=D("0")))
    assert res.totals.revenue.amount == 0
    assert res.totals.profit_margin_pct is None


# ---------------------------------------------------------------- scenarios


def test_scenarios_order_and_freight_factor() -> None:
    results = run_scenarios(case1_leather_bags_de())
    assert list(results) == ["pessimistic", "base", "optimistic"]
    p, b, o = (results[k].totals.net_profit.amount for k in ("pessimistic", "base", "optimistic"))
    assert p < b < o
    assert results["pessimistic"].line("main_freight").amount.amount == D("1440")  # type: ignore[union-attr]
    assert results["base"].totals.net_profit.rounded() == D("6029.77")
    assert isinstance(results["optimistic"].totals.quantity_sold, Decimal)
