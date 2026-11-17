"""Germany (EU customs union).

Customs value: transaction value plus transport, insurance and related costs up to the place
where goods enter the EU customs territory (Union Customs Code, Art. 70–71).
Import VAT base: customs value + duties + incidental costs (transport) up to the first place
of destination in the importing member state.

MVP simplification (shown to the user as a warning by the engine where relevant):
the whole main freight is treated as pre-border cost; the intra-EU leg is not separated.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..money import Money


@dataclass(frozen=True, slots=True)
class GermanyRulePack:
    country: str = "DE"
    currency: str = "EUR"
    version: str = "de-1"

    def customs_value(self, goods_value: Money, pre_border_costs: Money) -> Money:
        return goods_value + pre_border_costs

    def import_vat_base(self, customs_value: Money, duty: Money, post_border_costs: Money) -> Money:
        return customs_value + duty + post_border_costs

    def customs_value_note(self) -> str:
        return "EU: tovar qiymati + EU chegarasigacha transport, sug‘urta va bog‘liq xarajatlar"

    def import_vat_base_note(self) -> str:
        return "DE: bojxona qiymati + boj + birinchi manzilgacha transport xarajatlari"
