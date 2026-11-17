"""Landed cost and profitability calculation. Deterministic, no AI, no I/O.

See docs/08-calculation-logic.md for the formulas.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import ROUND_CEILING, Decimal

from .countries import CountryRulePack, get_rule_pack
from .incoterms import FULLY_AUTOMATED, POST_BORDER_IN_PRICE, PRE_BORDER, Incoterm, Party, Segment, payer
from .models import (
    FIXED_KINDS,
    LOGISTICS_SEGMENT,
    VARIABLE_KINDS,
    Basis,
    CalcInput,
    CalcResult,
    CalcWarning,
    CostKind,
    CostLine,
    DataClass,
    DutyAlternative,
    Mode,
    ResultLine,
    Totals,
    verification_to_class,
    weakest,
)
from .money import Money, money_sum

ENGINE_VERSION = "1.0.0"

LABELS: dict[str, str] = {
    "product_cost": "Mahsulot qiymati",
    "origin_inland": "Ichki transport (jo‘natish mamlakati)",
    "export_clearance": "Eksport rasmiylashtiruvi",
    "main_freight": "Xalqaro fraxt",
    "insurance": "Yuk sug‘urtasi",
    "import_clearance": "Import rasmiylashtiruvi (broker)",
    "dest_inland": "Manzilgacha yetkazish",
    "customs_duty": "Bojxona boji",
    "import_vat": "Import QQS",
    "warehouse": "Ombor",
    "advertising": "Reklama",
    "certification": "Sertifikatlash",
    "other_fixed": "Boshqa doimiy xarajatlar",
    "marketplace_fee": "Marketplace komissiyasi",
    "fulfillment": "Fulfillment / yetkazib berish (dona uchun)",
    "other_per_unit": "Boshqa o‘zgaruvchan xarajatlar",
}

HUNDRED = Decimal(100)


@dataclass
class _Ctx:
    inp: CalcInput
    currency: str
    user: Party
    warnings: list[CalcWarning] = field(default_factory=list)
    lines: list[ResultLine] = field(default_factory=list)
    complete: bool = True

    def warn(self, code: str, message: str) -> None:
        if all(w.code != code for w in self.warnings):
            self.warnings.append(CalcWarning(code, message))

    def to_cur(self, m: Money) -> Money:
        return self.inp.fx.convert(m, self.currency)


def calculate(inp: CalcInput) -> CalcResult:
    inp.fx.reset_usage()
    if inp.mode is Mode.IMPORT_RESELL:
        pack: CountryRulePack | None = get_rule_pack(inp.destination)
        assert pack is not None
        ctx = _Ctx(inp=inp, currency=pack.currency, user=Party.BUYER)
    else:
        # destination pack is needed only when the seller pays import taxes (DDP); still validate the country
        pack = get_rule_pack(inp.destination)
        ctx = _Ctx(inp=inp, currency=inp.sale_price.currency, user=Party.SELLER)

    _common_warnings(ctx)
    q = Decimal(inp.quantity)
    goods = ctx.to_cur(inp.unit_goods_value) * q
    ctx.lines.append(
        ResultLine(
            key="product_cost",
            label=LABELS["product_cost"] if inp.mode is Mode.IMPORT_RESELL else "Ishlab chiqarish tannarxi",
            amount=goods,
            per_unit=goods / q,
            data_class=DataClass.USER_PROVIDED,
            formula="unit_goods_value × quantity",
            in_landed_cost=True,
        )
    )

    logistics = _logistics_lines(ctx, goods, q)
    pre_border = money_sum([m for seg, m in logistics if seg in PRE_BORDER], ctx.currency)
    post_border = money_sum([m for seg, m in logistics if seg is Segment.DEST_INLAND], ctx.currency)
    logistics_total = money_sum([m for _, m in logistics], ctx.currency)

    duty, vat_cost, vat_recoverable = _import_taxes(ctx, pack, goods, pre_border, post_border, q)

    landed = goods + logistics_total + duty + vat_cost
    totals = _profitability(ctx, landed, goods, vat_recoverable, q)
    fx_used = tuple(inp.fx.used_rates())

    # Alternative duty regimes (e.g. MFN vs GSP+): full recalculation so the VAT base follows the duty.
    alternatives: list[DutyAlternative] = []
    if len(inp.duty_rates) > 1 and payer(inp.incoterm, Segment.IMPORT_DUTIES_TAXES) is ctx.user:
        for alt in inp.duty_rates[1:]:
            alt_result = calculate(replace(inp, duty_rates=(alt,)))
            alt_duty_line = alt_result.line("customs_duty")
            alternatives.append(
                DutyAlternative(
                    regime=alt.regime,
                    rate=alt.rate,
                    duty=alt_duty_line.amount if alt_duty_line else Money.zero(ctx.currency),
                    unit_landed_cost=alt_result.totals.unit_landed_cost,
                    verification=alt.verification,
                    conditions=alt.conditions,
                )
            )

    return CalcResult(
        engine_version=ENGINE_VERSION,
        mode=inp.mode,
        currency=ctx.currency,
        as_of=inp.as_of,
        rule_pack_version=pack.version if pack else None,
        lines=tuple(ctx.lines),
        totals=totals,
        duty_alternatives=tuple(alternatives),
        warnings=tuple(ctx.warnings),
        fx_rates_used=fx_used,
    )


# ---------------------------------------------------------------- steps


def _common_warnings(ctx: _Ctx) -> None:
    inp = ctx.inp
    if not inp.hs_code:
        ctx.warn("HS_CODE_MISSING", "HS kod ko‘rsatilmagan — boj stavkasini aniqlab bo‘lmaydi.")
    elif not inp.hs_confirmed:
        ctx.warn(
            "HS_CODE_NOT_CONFIRMED",
            "HS kod tasdiqlanmagan. Bu yakuniy tasnif emas — bojxona brokeri orqali tekshiring.",
        )
    if inp.incoterm not in FULLY_AUTOMATED:
        ctx.warn(
            "INCOTERM_REVIEW",
            f"{inp.incoterm} uchun xarajat taqsimoti shartnomadagi topshirish joyiga bog‘liq — qo‘lda tekshiring.",
        )


def _line_amount(ctx: _Ctx, cl: CostLine, goods: Money, q: Decimal) -> Money:
    if cl.basis is Basis.PERCENT_OF_GOODS:
        assert cl.rate is not None
        return goods * cl.rate
    assert cl.amount is not None
    m = ctx.to_cur(cl.amount)
    return m * q if cl.basis is Basis.PER_UNIT else m


def _formula(cl: CostLine) -> str:
    return {
        Basis.PER_SHIPMENT: "partiya uchun summa",
        Basis.PER_UNIT: "dona narxi × miqdor",
        Basis.PERCENT_OF_GOODS: f"tovar qiymati × {cl.rate}",
    }[cl.basis]


def _aggregate(
    ctx: _Ctx, key: str, items: list[tuple[CostLine, Money]], q: Decimal, in_landed: bool, per_unit_div: Decimal
) -> Money:
    total = money_sum([m for _, m in items], ctx.currency)
    sources = [cl.source for cl, _ in items if cl.source]
    ctx.lines.append(
        ResultLine(
            key=key,
            label=LABELS[key],
            amount=total,
            per_unit=total / per_unit_div if per_unit_div > 0 else None,
            data_class=weakest([cl.data_class for cl, _ in items]),
            formula="; ".join(sorted({_formula(cl) for cl, _ in items})),
            in_landed_cost=in_landed,
            source="; ".join(sources) or None,
        )
    )
    return total


def _logistics_lines(ctx: _Ctx, goods: Money, q: Decimal) -> list[tuple[Segment, Money]]:
    inp = ctx.inp
    by_kind: dict[CostKind, list[tuple[CostLine, Money]]] = {}
    for cl in inp.cost_lines:
        segment = LOGISTICS_SEGMENT.get(cl.kind)
        if segment is None:
            continue
        if payer(inp.incoterm, segment) is not ctx.user:
            ctx.warn(
                f"EXCLUDED_{cl.kind.value.upper()}",
                f"{LABELS[cl.kind.value]}: {inp.incoterm} shartida buni boshqa tomon to‘laydi — "
                "ikki marta hisoblanmasligi uchun chiqarib tashlandi.",
            )
            continue
        by_kind.setdefault(cl.kind, []).append((cl, _line_amount(ctx, cl, goods, q)))

    if payer(inp.incoterm, Segment.MAIN_FREIGHT) is ctx.user and CostKind.MAIN_FREIGHT not in by_kind:
        ctx.complete = False
        ctx.warn(
            "FREIGHT_MISSING",
            "Xalqaro fraxt sizning zimmangizda, lekin narxi kiritilmagan — landed cost to‘liq emas. "
            "Transport kompaniyasi taklifini kiriting.",
        )

    result: list[tuple[Segment, Money]] = []
    for kind in LOGISTICS_SEGMENT:  # stable output order
        if kind in by_kind:
            total = _aggregate(ctx, kind.value, by_kind[kind], q, in_landed=True, per_unit_div=q)
            result.append((LOGISTICS_SEGMENT[kind], total))
    return result


def _import_taxes(
    ctx: _Ctx,
    pack: CountryRulePack | None,
    goods: Money,
    pre_border: Money,
    post_border: Money,
    q: Decimal,
) -> tuple[Money, Money, Money]:
    """Returns (duty, non-recoverable VAT cost, recoverable VAT) in ctx currency. Applies duty_rates[0]."""
    inp = ctx.inp
    zero = Money.zero(ctx.currency)

    if payer(inp.incoterm, Segment.IMPORT_DUTIES_TAXES) is not ctx.user:
        if ctx.user is Party.SELLER:
            ctx.warn(
                "BUYER_PAYS_IMPORT_TAXES",
                f"{inp.incoterm} shartida import boji va QQSni xaridor to‘laydi — sizning xarajatingizga kirmaydi.",
            )
        else:
            ctx.warn(
                "SELLER_PAID_IMPORT_TAXES",
                "DDP: import boji va QQS yetkazib beruvchi narxiga kiritilgan deb hisoblandi.",
            )
        return zero, zero, zero

    assert pack is not None
    dcur = pack.currency

    # Customs value is computed in the destination currency, then converted to the reporting currency.
    def to_dest(m: Money) -> Money:
        return inp.fx.convert(m, dcur)

    def from_dest(m: Money) -> Money:
        return inp.fx.convert(m, ctx.currency)

    if ctx.user is Party.SELLER:
        # DDP export: the contract price already includes delivery to the final place,
        # so neither pre- nor post-border transport is added on top of it.
        cv_goods = to_dest(inp.sale_price * Decimal(inp.quantity))
        cv = pack.customs_value(cv_goods, Money.zero(dcur))
        post_border_dest = Money.zero(dcur)
    else:
        cv = pack.customs_value(to_dest(goods), to_dest(pre_border))
        post_border_dest = to_dest(post_border)

    if inp.incoterm in POST_BORDER_IN_PRICE:
        ctx.warn(
            "CUSTOMS_VALUE_APPROX",
            "Narxga chegaradan keyingi transport kiritilgan; bojxona qiymati biroz oshirib hisoblangan bo‘lishi mumkin.",
        )

    if not inp.duty_rates:
        ctx.complete = False
        ctx.warn(
            "DUTY_RATE_MISSING",
            "Bojxona boji stavkasi topilmadi — hisobga kiritilmadi. Stavkani rasmiy manbadan tekshirib kiriting.",
        )
        duty_dest = Money.zero(dcur)
    else:
        applied = inp.duty_rates[0]
        duty_dest = cv * applied.rate
        if applied.verification.value != "verified":
            ctx.warn(
                "DUTY_RATE_UNVERIFIED",
                f"Boj stavkasi ({applied.regime}) rasmiy manbada tasdiqlanmagan — taxminiy.",
            )
        if applied.conditions:
            ctx.warn(f"DUTY_CONDITIONS_{applied.regime}", f"{applied.regime}: {applied.conditions}")
        line_duty = from_dest(duty_dest)
        ctx.lines.append(
            ResultLine(
                key="customs_duty",
                label=f"{LABELS['customs_duty']} ({applied.regime}, {applied.rate * HUNDRED:.2f}%)",
                amount=line_duty,
                per_unit=line_duty / q,
                data_class=verification_to_class(applied.verification),
                formula=f"bojxona qiymati ({cv}) × stavka. {pack.customs_value_note()}",
                in_landed_cost=True,
                source=applied.source_url,
            )
        )

    duty = from_dest(duty_dest)

    taxes = inp.taxes
    if taxes is None or taxes.import_vat_rate is None:
        ctx.complete = False
        ctx.warn("IMPORT_VAT_MISSING", "Import QQS stavkasi kiritilmagan — hisobga kiritilmadi.")
        return duty, Money.zero(ctx.currency), Money.zero(ctx.currency)

    if taxes.verification.value != "verified":
        ctx.warn("TAX_RATE_UNVERIFIED", "QQS stavkasi rasmiy manbada tasdiqlanmagan — taxminiy.")

    base = pack.import_vat_base(cv, duty_dest, post_border_dest)
    vat = from_dest(base * taxes.import_vat_rate)
    recoverable = inp.importer_vat_registered
    ctx.lines.append(
        ResultLine(
            key="import_vat",
            label=f"{LABELS['import_vat']} ({taxes.import_vat_rate * HUNDRED:.2f}%)"
            + (" — qaytariladi" if recoverable else ""),
            amount=vat,
            per_unit=vat / q,
            data_class=verification_to_class(taxes.verification),
            formula=f"QQS bazasi × stavka. {pack.import_vat_base_note()}",
            in_landed_cost=not recoverable,
            recoverable=recoverable,
            source=taxes.source_url,
        )
    )
    if recoverable:
        ctx.warn(
            "IMPORT_VAT_RECOVERABLE",
            "Import QQS qaytariladi (QQS to‘lovchisi sifatida) — sof xarajatga qo‘shilmadi, "
            "lekin boshlang‘ich pul oqimiga (investitsiya) kiritildi.",
        )
        return duty, Money.zero(ctx.currency), vat
    return duty, vat, Money.zero(ctx.currency)


def _profitability(ctx: _Ctx, landed: Money, goods: Money, recoverable_vat: Money, q: Decimal) -> Totals:
    inp = ctx.inp
    cur = ctx.currency
    unit_landed = landed / q
    qs = q * inp.sell_through

    gross_price = ctx.to_cur(inp.sale_price)
    if inp.price_includes_vat:
        assert inp.taxes is not None and inp.taxes.sales_vat_rate is not None
        net_price = gross_price / (Decimal(1) + inp.taxes.sales_vat_rate)
    else:
        net_price = gross_price

    # variable selling costs per unit sold
    var_items: dict[CostKind, list[tuple[CostLine, Money]]] = {}
    fixed_items: dict[CostKind, list[tuple[CostLine, Money]]] = {}
    for cl in inp.cost_lines:
        if cl.kind in VARIABLE_KINDS:
            assert cl.amount is not None
            var_items.setdefault(cl.kind, []).append((cl, ctx.to_cur(cl.amount)))
        elif cl.kind in FIXED_KINDS:
            fixed_items.setdefault(cl.kind, []).append((cl, _line_amount(ctx, cl, goods, q)))

    fee_unit = gross_price * inp.marketplace_fee_rate
    var_unit = fee_unit
    if inp.marketplace_fee_rate > 0:
        fee_total = fee_unit * qs
        ctx.lines.append(
            ResultLine(
                key="marketplace_fee",
                label=f"{LABELS['marketplace_fee']} ({inp.marketplace_fee_rate * HUNDRED:.2f}%)",
                amount=fee_total,
                per_unit=fee_unit,
                data_class=DataClass.USER_PROVIDED,
                formula="yalpi (QQSli) sotuv narxi × komissiya × sotilgan miqdor",
                in_landed_cost=False,
            )
        )
    for kind in (CostKind.FULFILLMENT, CostKind.OTHER_PER_UNIT):
        if kind in var_items:
            unit = money_sum([m for _, m in var_items[kind]], cur)
            var_unit = var_unit + unit
            items = [(cl, m * qs) for cl, m in var_items[kind]]
            _aggregate(ctx, kind.value, items, q, in_landed=False, per_unit_div=qs)

    fixed = Money.zero(cur)
    for kind in (CostKind.WAREHOUSE, CostKind.ADVERTISING, CostKind.CERTIFICATION, CostKind.OTHER_FIXED):
        if kind in fixed_items:
            fixed = fixed + _aggregate(ctx, kind.value, fixed_items[kind], q, in_landed=False, per_unit_div=q)

    revenue = net_price * qs
    cogs = unit_landed * qs
    gross_profit = revenue - cogs
    variable_total = var_unit * qs
    net_profit = gross_profit - variable_total - fixed
    margin = net_profit.ratio(revenue) * HUNDRED if revenue.amount > 0 else None
    investment = landed + fixed + recoverable_vat
    roi = net_profit.ratio(investment) * HUNDRED if investment.amount > 0 else None
    contribution = net_price - unit_landed - var_unit

    break_even: int | None
    if contribution.amount <= 0:
        break_even = None
        ctx.warn(
            "NO_BREAK_EVEN",
            "Har bir sotilgan dona zarar keltiradi (narx − tannarx − o‘zgaruvchan xarajatlar ≤ 0). "
            "Zararsizlik nuqtasi yo‘q.",
        )
    else:
        break_even = int(fixed.ratio(contribution).to_integral_value(rounding=ROUND_CEILING)) if fixed.amount else 0
        if break_even > inp.quantity:
            ctx.warn(
                "BREAK_EVEN_ABOVE_QUANTITY",
                f"Zararsizlik uchun {break_even} dona sotish kerak — bu partiyadan ({inp.quantity}) ko‘p.",
            )

    if inp.sell_through < 1:
        ctx.warn(
            "UNSOLD_INVENTORY",
            "Sotilmagan qoldiq tannarx bo‘yicha zaxirada qoladi; foyda faqat sotilgan dona uchun hisoblangan.",
        )

    return Totals(
        quantity=inp.quantity,
        quantity_sold=qs,
        goods_value=goods,
        total_landed_cost=landed,
        unit_landed_cost=unit_landed,
        gross_unit_price=gross_price,
        net_unit_price=net_price,
        revenue=revenue,
        cogs=cogs,
        gross_profit=gross_profit,
        variable_cost_per_unit=var_unit,
        variable_selling_costs=variable_total,
        fixed_costs=fixed,
        net_profit=net_profit,
        profit_margin_pct=margin,
        recoverable_vat=recoverable_vat,
        total_investment=investment,
        roi_pct=roi,
        contribution_per_unit=contribution,
        break_even_units=break_even,
        is_complete=ctx.complete,
    )


__all__ = ["ENGINE_VERSION", "Incoterm", "calculate"]
