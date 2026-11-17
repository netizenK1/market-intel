"""Input and output models of the calculation engine (pure dataclasses, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum

from .fx import FxRate, FxTable
from .incoterms import Incoterm, Segment
from .money import D, Money


class CalcInputError(ValueError):
    """Input cannot be calculated (as opposed to warnings, which allow a partial result)."""


class Mode(StrEnum):
    IMPORT_RESELL = "import_resell"  # user imports into destination and resells there
    EXPORT_SALE = "export_sale"  # user sells to a foreign buyer under an Incoterm


class DataClass(StrEnum):
    VERIFIED = "verified"
    OBSERVED = "observed"
    USER_PROVIDED = "user_provided"
    ESTIMATED = "estimated"
    MOCK = "mock"


# Lower index = less trustworthy. Aggregates take the weakest class of their inputs.
_TRUST_ORDER = [DataClass.MOCK, DataClass.ESTIMATED, DataClass.USER_PROVIDED, DataClass.OBSERVED, DataClass.VERIFIED]


def weakest(classes: list[DataClass]) -> DataClass:
    return min(classes, key=_TRUST_ORDER.index)


class Verification(StrEnum):
    VERIFIED = "verified"  # checked against an official source, has verified_at
    UNVERIFIED = "unverified"  # from a source but not yet checked
    USER_PROVIDED = "user_provided"


def verification_to_class(v: Verification) -> DataClass:
    return {
        Verification.VERIFIED: DataClass.VERIFIED,
        Verification.UNVERIFIED: DataClass.ESTIMATED,
        Verification.USER_PROVIDED: DataClass.USER_PROVIDED,
    }[v]


class CostKind(StrEnum):
    # logistics chain (payer decided by Incoterm)
    ORIGIN_INLAND = "origin_inland"
    EXPORT_CLEARANCE = "export_clearance"
    MAIN_FREIGHT = "main_freight"
    INSURANCE = "insurance"
    IMPORT_CLEARANCE = "import_clearance"
    DEST_INLAND = "dest_inland"
    # fixed costs of the operation
    WAREHOUSE = "warehouse"
    ADVERTISING = "advertising"
    CERTIFICATION = "certification"
    OTHER_FIXED = "other_fixed"
    # variable selling costs, per unit SOLD
    FULFILLMENT = "fulfillment"
    OTHER_PER_UNIT = "other_per_unit"


LOGISTICS_SEGMENT: dict[CostKind, Segment] = {
    CostKind.ORIGIN_INLAND: Segment.ORIGIN_INLAND,
    CostKind.EXPORT_CLEARANCE: Segment.EXPORT_CLEARANCE,
    CostKind.MAIN_FREIGHT: Segment.MAIN_FREIGHT,
    CostKind.INSURANCE: Segment.INSURANCE,
    CostKind.IMPORT_CLEARANCE: Segment.IMPORT_CLEARANCE,
    CostKind.DEST_INLAND: Segment.DEST_INLAND,
}
FIXED_KINDS = frozenset({CostKind.WAREHOUSE, CostKind.ADVERTISING, CostKind.CERTIFICATION, CostKind.OTHER_FIXED})
VARIABLE_KINDS = frozenset({CostKind.FULFILLMENT, CostKind.OTHER_PER_UNIT})


class Basis(StrEnum):
    PER_SHIPMENT = "per_shipment"
    PER_UNIT = "per_unit"  # logistics/fixed: per purchased unit; variable: per sold unit
    PERCENT_OF_GOODS = "percent_of_goods"  # e.g. cargo insurance


@dataclass(frozen=True, slots=True)
class CostLine:
    kind: CostKind
    basis: Basis
    amount: Money | None = None
    rate: Decimal | None = None
    data_class: DataClass = DataClass.USER_PROVIDED
    source: str | None = None

    def __post_init__(self) -> None:
        if self.basis is Basis.PERCENT_OF_GOODS:
            if self.rate is None or self.amount is not None:
                raise CalcInputError(f"{self.kind}: percent basis needs `rate` and no `amount`")
            object.__setattr__(self, "rate", D(self.rate))
            assert self.rate is not None
            if not (0 <= self.rate <= 1):
                raise CalcInputError(f"{self.kind}: rate must be between 0 and 1")
            if self.kind not in LOGISTICS_SEGMENT:
                raise CalcInputError(f"{self.kind}: percent basis is only allowed for logistics costs")
        else:
            if self.amount is None or self.rate is not None:
                raise CalcInputError(f"{self.kind}: `amount` is required for basis {self.basis}")
            if self.amount.amount < 0:
                raise CalcInputError(f"{self.kind}: amount must not be negative")
        if self.kind in VARIABLE_KINDS and self.basis is not Basis.PER_UNIT:
            raise CalcInputError(f"{self.kind}: variable selling costs must use per_unit basis")


@dataclass(frozen=True, slots=True)
class DutyRate:
    regime: str  # MFN, GSP_PLUS, ...
    rate: Decimal  # ad valorem, 0.03 = 3 %
    verification: Verification
    source_url: str | None = None
    conditions: str | None = None  # e.g. "proof of origin (REX) required"

    def __post_init__(self) -> None:
        object.__setattr__(self, "rate", D(self.rate))
        if not (0 <= self.rate <= 10):
            raise CalcInputError("duty rate out of range")
        if self.verification is Verification.VERIFIED and not self.source_url:
            raise CalcInputError("a verified duty rate must have a source_url")


@dataclass(frozen=True, slots=True)
class TaxRates:
    verification: Verification
    import_vat_rate: Decimal | None = None
    sales_vat_rate: Decimal | None = None
    source_url: str | None = None

    def __post_init__(self) -> None:
        for name in ("import_vat_rate", "sales_vat_rate"):
            v = getattr(self, name)
            if v is not None:
                v = D(v)
                if not (0 <= v <= 1):
                    raise CalcInputError(f"{name} out of range")
                object.__setattr__(self, name, v)
        if self.verification is Verification.VERIFIED and not self.source_url:
            raise CalcInputError("verified tax rates must have a source_url")


@dataclass(frozen=True, slots=True)
class CalcInput:
    mode: Mode
    destination: str  # ISO country code of the import market
    incoterm: Incoterm
    quantity: int
    unit_goods_value: Money  # import: purchase price under the Incoterm; export: own production cost
    sale_price: Money  # import: resale price in destination; export: contract price under the Incoterm
    as_of: date
    fx: FxTable
    price_includes_vat: bool = False
    importer_vat_registered: bool = False  # can the party paying import VAT reclaim it?
    duty_rates: tuple[DutyRate, ...] = ()  # first = applied, others = shown as alternatives
    taxes: TaxRates | None = None
    cost_lines: tuple[CostLine, ...] = ()
    marketplace_fee_rate: Decimal = Decimal(0)  # share of the gross (VAT-inclusive) price
    sell_through: Decimal = Decimal(1)  # share of quantity expected to be sold
    hs_code: str | None = None
    hs_confirmed: bool = False

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise CalcInputError("quantity must be positive")
        if self.unit_goods_value.amount < 0 or self.sale_price.amount < 0:
            raise CalcInputError("prices must not be negative")
        object.__setattr__(self, "marketplace_fee_rate", D(self.marketplace_fee_rate))
        object.__setattr__(self, "sell_through", D(self.sell_through))
        if not (0 <= self.marketplace_fee_rate < 1):
            raise CalcInputError("marketplace_fee_rate must be in [0, 1)")
        if not (0 <= self.sell_through <= 1):
            raise CalcInputError("sell_through must be in [0, 1]")
        if self.price_includes_vat and (self.taxes is None or self.taxes.sales_vat_rate is None):
            raise CalcInputError("price_includes_vat requires taxes.sales_vat_rate")


# ---------------------------------------------------------------- results


@dataclass(frozen=True, slots=True)
class ResultLine:
    key: str
    label: str
    amount: Money  # whole batch
    per_unit: Money | None
    data_class: DataClass
    formula: str
    in_landed_cost: bool
    recoverable: bool = False
    source: str | None = None


@dataclass(frozen=True, slots=True)
class CalcWarning:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class DutyAlternative:
    regime: str
    rate: Decimal
    duty: Money
    unit_landed_cost: Money
    verification: Verification
    conditions: str | None


@dataclass(frozen=True, slots=True)
class Totals:
    quantity: int
    quantity_sold: Decimal
    goods_value: Money
    total_landed_cost: Money
    unit_landed_cost: Money
    gross_unit_price: Money
    net_unit_price: Money
    revenue: Money
    cogs: Money
    gross_profit: Money
    variable_cost_per_unit: Money
    variable_selling_costs: Money
    fixed_costs: Money
    net_profit: Money
    profit_margin_pct: Decimal | None
    recoverable_vat: Money
    total_investment: Money
    roi_pct: Decimal | None
    contribution_per_unit: Money
    break_even_units: int | None
    is_complete: bool  # False when a required cost (freight, duty, VAT) is missing


@dataclass(frozen=True, slots=True)
class CalcResult:
    engine_version: str
    mode: Mode
    currency: str
    as_of: date
    rule_pack_version: str | None
    lines: tuple[ResultLine, ...]
    totals: Totals
    duty_alternatives: tuple[DutyAlternative, ...]
    warnings: tuple[CalcWarning, ...]
    fx_rates_used: tuple[FxRate, ...] = field(default=())

    def line(self, key: str) -> ResultLine | None:
        return next((ln for ln in self.lines if ln.key == key), None)

    def warning_codes(self) -> set[str]:
        return {w.code for w in self.warnings}
