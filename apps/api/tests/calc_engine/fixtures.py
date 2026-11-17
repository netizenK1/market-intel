"""Test inputs. ALL RATES HERE ARE TEST FIXTURES, NOT REAL TARIFFS OR FX RATES.

Expected values in the golden tests were computed by hand (docs/08-calculation-logic.md, section 7)
independently of the engine code.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

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
    Money,
    TaxRates,
    Verification,
    fx,
)

AS_OF = date(2026, 11, 17)
FIXTURE_URL = "https://example.test/fixture"


def eur(x: str) -> Money:
    return Money(D(x), "EUR")


def usd(x: str) -> Money:
    return Money(D(x), "USD")


def aed(x: str) -> Money:
    return Money(D(x), "AED")


def fx_table() -> FxTable:
    return FxTable(
        [
            fx("EUR", "USD", "1.08", AS_OF, "fixture"),
            fx("USD", "AED", "3.6725", AS_OF, "fixture"),
        ]
    )


DE_TAXES = TaxRates(
    verification=Verification.VERIFIED,
    import_vat_rate=D("0.19"),
    sales_vat_rate=D("0.19"),
    source_url=FIXTURE_URL,
)
MFN_3 = DutyRate("MFN", D("0.03"), Verification.VERIFIED, FIXTURE_URL)
GSP_PLUS_0 = DutyRate(
    "GSP_PLUS", D("0"), Verification.VERIFIED, FIXTURE_URL, conditions="REX kelib chiqish dalili kerak"
)


def case1_leather_bags_de(**overrides: object) -> CalcInput:
    """PRD test case 1: leather bags, UZ -> DE, 500 pcs x $15, sale EUR 55 incl. VAT, EXW."""
    base = CalcInput(
        mode=Mode.IMPORT_RESELL,
        destination="DE",
        incoterm=Incoterm.EXW,
        quantity=500,
        unit_goods_value=usd("15"),
        sale_price=eur("55"),
        price_includes_vat=True,
        importer_vat_registered=True,
        as_of=AS_OF,
        fx=fx_table(),
        hs_code="420221",
        hs_confirmed=True,
        duty_rates=(MFN_3, GSP_PLUS_0),
        taxes=DE_TAXES,
        cost_lines=(
            CostLine(CostKind.EXPORT_CLEARANCE, Basis.PER_SHIPMENT, eur("150")),
            CostLine(CostKind.MAIN_FREIGHT, Basis.PER_SHIPMENT, eur("1200")),
            CostLine(CostKind.INSURANCE, Basis.PER_SHIPMENT, eur("40")),
            CostLine(CostKind.IMPORT_CLEARANCE, Basis.PER_SHIPMENT, eur("120")),
            CostLine(CostKind.DEST_INLAND, Basis.PER_SHIPMENT, eur("200")),
            CostLine(CostKind.FULFILLMENT, Basis.PER_UNIT, eur("3.50")),
            CostLine(CostKind.ADVERTISING, Basis.PER_SHIPMENT, eur("2000")),
            CostLine(CostKind.WAREHOUSE, Basis.PER_SHIPMENT, eur("300")),
        ),
        marketplace_fee_rate=D("0.15"),
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def case2_textile_ae(**overrides: object) -> CalcInput:
    """PRD test case 2: textile, UZ -> AE, 1000 pcs, CIF, sale AED 39 incl. VAT."""
    base = CalcInput(
        mode=Mode.IMPORT_RESELL,
        destination="AE",
        incoterm=Incoterm.CIF,
        quantity=1000,
        unit_goods_value=usd("4"),
        sale_price=aed("39"),
        price_includes_vat=True,
        importer_vat_registered=True,
        as_of=AS_OF,
        fx=fx_table(),
        hs_code="610910",
        hs_confirmed=False,
        duty_rates=(DutyRate("MFN", D("0.05"), Verification.UNVERIFIED, FIXTURE_URL),),
        taxes=TaxRates(Verification.VERIFIED, D("0.05"), D("0.05"), FIXTURE_URL),
        cost_lines=(
            CostLine(CostKind.MAIN_FREIGHT, Basis.PER_SHIPMENT, aed("2000")),  # seller pays under CIF
            CostLine(CostKind.IMPORT_CLEARANCE, Basis.PER_SHIPMENT, aed("500")),
            CostLine(CostKind.DEST_INLAND, Basis.PER_SHIPMENT, aed("300")),
        ),
        sell_through=D("0.85"),
    )
    return replace(base, **overrides)  # type: ignore[arg-type]
