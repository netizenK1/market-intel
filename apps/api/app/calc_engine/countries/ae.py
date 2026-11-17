"""United Arab Emirates (GCC Common Customs Law).

Customs value: CIF value (goods + freight + insurance to the point of entry).
Import VAT base: customs value + customs duty (+ excise, when applicable — not modelled in MVP).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..money import Money


@dataclass(frozen=True, slots=True)
class UaeRulePack:
    country: str = "AE"
    currency: str = "AED"
    version: str = "ae-1"

    def customs_value(self, goods_value: Money, pre_border_costs: Money) -> Money:
        return goods_value + pre_border_costs

    def import_vat_base(self, customs_value: Money, duty: Money, post_border_costs: Money) -> Money:
        # Post-border inland transport is not part of the UAE import VAT base.
        return customs_value + duty

    def customs_value_note(self) -> str:
        return "BAA/GCC: CIF qiymati (tovar + kirish nuqtasigacha fraxt va sug‘urta)"

    def import_vat_base_note(self) -> str:
        return "BAA: bojxona qiymati + boj"
