"""Deterministic landed-cost and profitability engine.

Rules: no AI, no database, no network. Decimal only. Rates are passed in by the caller.
"""

from .countries import UnsupportedCountryError, get_rule_pack, supported_countries
from .engine import ENGINE_VERSION, calculate
from .fx import FxRate, FxTable, MissingFxRateError, fx
from .incoterms import Incoterm, Party, Segment, payer
from .models import (
    Basis,
    CalcInput,
    CalcInputError,
    CalcResult,
    CostKind,
    CostLine,
    DataClass,
    DutyRate,
    Mode,
    TaxRates,
    Verification,
)
from .money import D, Money
from .scenarios import DEFAULT_SCENARIOS, Scenario, run_scenarios

__all__ = [
    "DEFAULT_SCENARIOS",
    "ENGINE_VERSION",
    "Basis",
    "CalcInput",
    "CalcInputError",
    "CalcResult",
    "CostKind",
    "CostLine",
    "D",
    "DataClass",
    "DutyRate",
    "FxRate",
    "FxTable",
    "Incoterm",
    "MissingFxRateError",
    "Mode",
    "Money",
    "Party",
    "Scenario",
    "Segment",
    "TaxRates",
    "UnsupportedCountryError",
    "Verification",
    "calculate",
    "fx",
    "get_rule_pack",
    "payer",
    "run_scenarios",
    "supported_countries",
]
