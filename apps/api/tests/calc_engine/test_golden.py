"""Golden tests: expected numbers computed by hand, independently of the engine."""

from __future__ import annotations

from decimal import Decimal

from app.calc_engine import (
    Basis,
    CalcInput,
    CostKind,
    CostLine,
    D,
    DutyRate,
    FxTable,
    Incoterm,
    Mode,
    TaxRates,
    Verification,
    calculate,
)

from .fixtures import AS_OF, FIXTURE_URL, case1_leather_bags_de, case2_textile_ae, fx_table, usd


def r2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"))


class TestCase1LeatherBagsGermany:
    def test_landed_cost_vat_registered(self) -> None:
        res = calculate(case1_leather_bags_de())
        t = res.totals
        assert res.currency == "EUR"
        assert t.goods_value.rounded() == D("6944.44")
        assert res.line("customs_duty").amount.rounded() == D("250.03")  # type: ignore[union-attr]
        vat = res.line("import_vat")
        assert vat is not None and vat.amount.rounded() == D("1669.05")
        assert vat.recoverable and not vat.in_landed_cost
        assert t.total_landed_cost.rounded() == D("8904.48")
        assert t.unit_landed_cost.rounded() == D("17.81")
        assert t.is_complete

    def test_vat_inclusive_price_is_netted(self) -> None:
        t = calculate(case1_leather_bags_de()).totals
        assert t.gross_unit_price.rounded() == D("55.00")
        assert t.net_unit_price.rounded() == D("46.22")  # 55 / 1.19

    def test_profitability(self) -> None:
        t = calculate(case1_leather_bags_de()).totals
        assert t.revenue.rounded() == D("23109.24")
        assert t.gross_profit.rounded() == D("14204.77")
        assert t.variable_cost_per_unit.rounded() == D("11.75")  # 15% x 55 + 3.50
        assert t.variable_selling_costs.rounded() == D("5875.00")
        assert t.fixed_costs.rounded() == D("2300.00")
        assert t.net_profit.rounded() == D("6029.77")
        assert t.profit_margin_pct is not None and r2(t.profit_margin_pct) == D("26.09")
        assert t.recoverable_vat.rounded() == D("1669.05")
        assert t.total_investment.rounded() == D("12873.53")
        assert t.roi_pct is not None and r2(t.roi_pct) == D("46.84")
        assert t.contribution_per_unit.rounded() == D("16.66")
        assert t.break_even_units == 139

    def test_vat_not_registered_adds_vat_to_cost(self) -> None:
        res = calculate(case1_leather_bags_de(importer_vat_registered=False))
        t = res.totals
        vat = res.line("import_vat")
        assert vat is not None and vat.in_landed_cost and not vat.recoverable
        assert t.total_landed_cost.rounded() == D("10573.53")
        assert t.unit_landed_cost.rounded() == D("21.15")
        assert t.recoverable_vat.amount == 0
        assert t.total_investment.rounded() == D("12873.53")
        assert t.net_profit.rounded() == D("4360.72")

    def test_gsp_plus_alternative_is_fully_recalculated(self) -> None:
        res = calculate(case1_leather_bags_de())
        [alt] = res.duty_alternatives
        assert alt.regime == "GSP_PLUS"
        assert alt.duty.amount == 0
        assert alt.unit_landed_cost.rounded() == D("17.31")  # 8654.44 / 500
        assert "DUTY_CONDITIONS_GSP_PLUS" not in res.warning_codes()  # conditions belong to the alternative

    def test_fx_rates_used_are_reported(self) -> None:
        res = calculate(case1_leather_bags_de())
        assert [(r.base, r.quote) for r in res.fx_rates_used] == [("EUR", "USD")]


class TestCase2TextileUae:
    def test_cif_freight_is_not_double_counted(self) -> None:
        res = calculate(case2_textile_ae())
        assert res.line("main_freight") is None
        assert "EXCLUDED_MAIN_FREIGHT" in res.warning_codes()

    def test_landed_cost(self) -> None:
        res = calculate(case2_textile_ae())
        t = res.totals
        assert res.currency == "AED"
        assert t.goods_value.rounded() == D("14690.00")
        assert res.line("customs_duty").amount.rounded() == D("734.50")  # type: ignore[union-attr]
        assert res.line("import_vat").amount.rounded() == D("771.23")  # type: ignore[union-attr]  # (14690+734.5) x 5%
        assert t.total_landed_cost.rounded() == D("16224.50")
        assert t.unit_landed_cost.rounded() == D("16.22")

    def test_profit_with_partial_sell_through(self) -> None:
        res = calculate(case2_textile_ae())
        t = res.totals
        assert t.quantity_sold == D("850")
        assert t.net_unit_price.rounded() == D("37.14")
        assert t.revenue.rounded() == D("31571.43")
        assert t.cogs.rounded() == D("13790.83")
        assert t.net_profit.rounded() == D("17780.60")
        assert t.break_even_units == 0
        assert {"UNSOLD_INVENTORY", "DUTY_RATE_UNVERIFIED", "HS_CODE_NOT_CONFIRMED"} <= res.warning_codes()


class TestExportSale:
    def _fob(self) -> CalcInput:
        return CalcInput(
            mode=Mode.EXPORT_SALE,
            destination="DE",
            incoterm=Incoterm.FOB,
            quantity=500,
            unit_goods_value=usd("15"),
            sale_price=usd("22"),
            as_of=AS_OF,
            fx=FxTable(),
            hs_code="420221",
            hs_confirmed=True,
            cost_lines=(
                CostLine(CostKind.ORIGIN_INLAND, Basis.PER_SHIPMENT, usd("100")),
                CostLine(CostKind.EXPORT_CLEARANCE, Basis.PER_SHIPMENT, usd("150")),
                CostLine(CostKind.MAIN_FREIGHT, Basis.PER_SHIPMENT, usd("900")),  # buyer pays under FOB
            ),
        )

    def test_fob_export(self) -> None:
        res = calculate(self._fob())
        t = res.totals
        assert res.currency == "USD"
        assert t.total_landed_cost.rounded() == D("7750.00")
        assert t.unit_landed_cost.rounded() == D("15.50")
        assert t.revenue.rounded() == D("11000.00")
        assert t.net_profit.rounded() == D("3250.00")
        assert t.profit_margin_pct is not None and r2(t.profit_margin_pct) == D("29.55")
        assert t.roi_pct is not None and r2(t.roi_pct) == D("41.94")
        assert {"BUYER_PAYS_IMPORT_TAXES", "EXCLUDED_MAIN_FREIGHT"} <= res.warning_codes()
        assert res.line("customs_duty") is None

    def test_ddp_export_seller_pays_duty_and_vat(self) -> None:
        inp = CalcInput(
            mode=Mode.EXPORT_SALE,
            destination="DE",
            incoterm=Incoterm.DDP,
            quantity=100,
            unit_goods_value=usd("10"),
            sale_price=usd("30"),
            as_of=AS_OF,
            fx=fx_table(),
            hs_code="420221",
            hs_confirmed=True,
            duty_rates=(DutyRate("MFN", D("0.03"), Verification.VERIFIED, FIXTURE_URL),),
            taxes=TaxRates(Verification.VERIFIED, D("0.19"), D("0.19"), FIXTURE_URL),
            importer_vat_registered=False,
            cost_lines=(
                CostLine(CostKind.MAIN_FREIGHT, Basis.PER_SHIPMENT, usd("500")),
                CostLine(CostKind.DEST_INLAND, Basis.PER_SHIPMENT, usd("100")),
            ),
        )
        res = calculate(inp)
        assert res.line("customs_duty").amount.rounded() == D("90.00")  # type: ignore[union-attr]
        assert res.line("import_vat").amount.rounded() == D("587.10")  # type: ignore[union-attr]
        assert res.totals.total_landed_cost.rounded() == D("2277.10")
        assert res.totals.net_profit.rounded() == D("722.90")
        assert "CUSTOMS_VALUE_APPROX" in res.warning_codes()
