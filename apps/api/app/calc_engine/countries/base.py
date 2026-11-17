"""Country rule pack contract. One pack per country; rules are NEVER shared implicitly between countries.

Packs encode the *structure* of the calculation (what is in the customs value, what is in the VAT base).
Rates come from the caller (DB tables with source URL + validity) — never from code.
"""

from __future__ import annotations

from typing import Protocol

from ..money import Money


class UnsupportedCountryError(LookupError):
    pass


class CountryRulePack(Protocol):
    @property
    def country(self) -> str: ...

    @property
    def currency(self) -> str: ...

    @property
    def version(self) -> str: ...

    def customs_value(self, goods_value: Money, pre_border_costs: Money) -> Money:
        """Value on which ad valorem duty is charged, in the pack currency."""
        ...

    def import_vat_base(self, customs_value: Money, duty: Money, post_border_costs: Money) -> Money:
        """Taxable amount for import VAT, in the pack currency."""
        ...

    def customs_value_note(self) -> str: ...

    def import_vat_base_note(self) -> str: ...
