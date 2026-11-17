# 08. Import/Export Calculation Logic

`calc_engine` — AI’siz, DB’siz, tarmoqsiz sof Python. Barcha qiymatlar `Decimal`. Yaxlitlash faqat **ko‘rsatishda** (2 xona), oraliq hisoblarda emas; bojxona summalari mamlakat qoidasiga ko‘ra yaxlitlanadi (rule pack ichida).

## 1. Kirish modeli (`CalcInput`)

```
product:      name, hs_code, hs_confirmed: bool, origin_country, unit_weight_kg, unit_volume_m3
quantity:     int
unit_cost:    Money (masalan 15 USD)            -- user_provided
destination:  country_code (DE | AE)
incoterm:     EXW | FCA | FOB | CIF | CPT | CIP | DAP | DDP
role:         'exporter' | 'importer'           -- kim nuqtai nazaridan hisoblaymiz
importer_vat_registered: bool                   -- import QQS qaytariladimi
channel:      'marketplace' | 'wholesale' | 'own_store'
sale_price:   Money, price_includes_vat: bool   -- masalan 55 EUR, true (B2C DE)
cost_lines[]: {segment, amount: Money, basis: per_unit|per_shipment|percent, data_class, source}
              segmentlar: export_clearance, origin_inland, main_freight, insurance,
              import_clearance(broker), dest_inland, warehouse, marketplace_fee(percent),
              fulfillment, advertising, certification, other
as_of_date:   date
fx_rates:     tashqaridan beriladi (manba va sana bilan)
tariff:       {rate, regime, verification_status, source}    -- yoki user_provided
tax_rules:    import_vat_rate, vat_rate, ...
```

## 2. Incoterms — ikki marta hisoblamaslik

Har segment uchun matritsa: kim to‘laydi (S = sotuvchi, B = xaridor) va u bojxona qiymatiga kiradimi.

| Segment | EXW | FCA | FOB | CIF | CPT | CIP | DAP | DDP |
|---|---|---|---|---|---|---|---|---|
| Eksport rasmiylashtiruvi | B | S | S | S | S | S | S | S |
| Asosiy fraxt | B | B | B | S | S | S | S | S |
| Sug‘urta (asosiy) | B* | B* | B* | S | B* | S | S* | S* |
| Import rasmiylashtiruvi, boj, import QQS | B | B | B | B | B | B | B | **S** |
| Manzilgacha yetkazish | B | B | B | B | B | B | S | S |

\* majburiy emas, odatda shu tomon.

Qoida: `role` va `incoterm` asosida har `cost_line` uchun `payer` aniqlanadi. Foydalanuvchining xarajatlari = faqat `payer == role` bo‘lgan qatorlar. Sotuv narxi Incoterm’ga ko‘ra qaysi xarajatlarni “ichiga olgan” bo‘lsa, o‘sha qatorlar qayta qo‘shilmaydi. MVP’da to‘liq avtomatlashtirilgan: EXW, FOB, CIF, DAP, DDP; qolganlari ma’lumotlar modelida bor, UI’da “qo‘lda” rejim.

## 3. Mamlakat qoidalari (rule packs)

### DE (EU)
- **Bojxona qiymati (CV)** = tranzaksiya qiymati + EU chegarasigacha fraxt + sug‘urta (ya’ni CIF EU chegarasi), EUR’ga konvertatsiya qilingan.
- **Boj** = CV × stavka (TARIC; kelib chiqish UZ bo‘lsa GSP+ preferensiyasi **faqat** kelib chiqish dalili shartlari bajarilganda qo‘llanadi — aks holda MFN; ikkala variant ko‘rsatiladi).
- **Import QQS bazasi** = CV + boj + EU ichidagi birinchi manzilgacha transport xarajatlari (+ aksiz bo‘lsa).
- **Import QQS** = baza × stavka. `importer_vat_registered=true` bo‘lsa — pul oqimida xarajat (cash-flow), lekin **sof foydaga qo‘shilmaydi** (qaytariladigan), alohida “QQS (qaytariladi)” qatori sifatida ko‘rsatiladi.
- **B2C sotuv**: Germaniyada iste’molchi narxi QQS bilan. `sale_price` QQSli bo‘lsa → **sof tushum = narx / (1 + QQS stavkasi)**. Masalan, €55 → €55 / 1.19 = **€46.22** (agar standart stavka qo‘llansa). Bu eng ko‘p uchraydigan xato — dastlabki hisob tushumni ~16% oshirib ko‘rsatadi.
- Stavkalarning o‘zi kodda emas — `customs_tariffs` / `tax_rules` jadvalidan, manba va sana bilan.

### AE (GCC)
- **Bojxona qiymati** = CIF qiymati (AED).
- **Boj** = CV × stavka (GCC umumiy tarif; ayrim tovarlar uchun istisno/ozod).
- **Import QQS bazasi** = CV + boj (+ aksiz bo‘lsa). Ro‘yxatdan o‘tgan importyor uchun reverse charge mexanizmi bo‘lishi mumkin — rule pack’da `recoverable_if` orqali.
- B2C narx QQSni o‘z ichiga oladi deb qabul qilinadi (BAA qoidasi bo‘yicha tekshiriladi).

## 4. Formulalar

```
FX:                   har bir Money manzil valyutasiga as_of_date kursi bilan; kurs manbasi natijada saqlanadi
Product cost (batch)  = unit_cost × quantity
Freight/insurance     = cost_lines (per_shipment yoki per_unit × quantity)
Customs value         = rule_pack.customs_value(...)
Duty                  = rule_pack.duty(customs_value, tariff)
Import VAT            = rule_pack.import_vat(...)                 -> recoverable? flag
Landed cost (batch)   = product + freight + insurance + duty + clearance + dest_inland
                        + import_vat (faqat qaytarilmasa)   [faqat payer==role]
                        (sertifikatlash, ombor, reklama — doimiy xarajatlar, landed cost’ga kirmaydi)
Customs value (DE/AE) = tovar qiymati + chegaragacha xaridor to‘lagan xarajatlar
                        (ichki transport, eksport rasmiylashtiruvi, fraxt, sug‘urta)
Unit landed cost      = landed_cost_batch / quantity
Net revenue per unit  = sale_price / (1+vat) agar price_includes_vat, aks holda sale_price
Variable selling cost = marketplace_fee% × gross_price + fulfillment + per-unit advertising
Contribution/unit     = net_revenue_unit − unit_landed_cost − variable_selling_cost_unit
Revenue (batch)       = net_revenue_unit × quantity_sold
Gross profit          = revenue − landed_cost_of_sold_units
Operating costs       = advertising (fixed) + warehouse + other fixed
Net profit            = gross_profit − variable_selling_costs − operating_costs     (soliqdan oldin)
Profit margin %       = net_profit / revenue × 100
Total investment      = landed_cost_batch + upfront fixed costs (sertifikat, reklama boshlanishi, import QQS cash-flow)
ROI %                 = net_profit / total_investment × 100
Break-even qty        = fixed_costs / contribution_per_unit    (contribution ≤ 0 bo‘lsa → “zararsizlik nuqtasi yo‘q”)
```

Eslatma: marketplace komissiyasi odatda QQSli yalpi narxdan olinadi — shuning uchun `gross_price` dan hisoblanadi.

## 5. Ssenariylar

Standart 3 ssenariy: **pessimistik / bazaviy / optimistik** — o‘zgaruvchilar: sotilgan ulush (masalan 60/85/100%), narx (−10%/0/+10%), fraxt (+20%/0/−10%). Foydalanuvchi o‘zgartirishi mumkin. Har ssenariy `estimated`.

## 6. Natija (`CalcResult`)

Har bir qator: `key`, `label`, `amount (batch)`, `amount_per_unit`, `currency`, `payer`, `data_class`, `source`, `formula`, `included_in_landed_cost: bool`, `recoverable: bool`.

Qatorlar: Product cost · Freight · Insurance · Customs duty · Import VAT · Customs clearance · Warehouse · Marketplace fee · Advertising · Other · **Total landed cost** · **Unit landed cost** · Expected revenue · Estimated profit · Margin · Break-even · ROI.

Qo‘shimcha: `warnings[]` — masalan “HS kod tasdiqlanmagan”, “Tarif `unverified`”, “Fraxt — foydalanuvchi taxmini”, “GSP+ kelib chiqish dalili talab qilinadi”.

## 7. Test keys 1 (PRD 17) — hisob tuzilishi (namunaviy, real statistika emas)

Kirish: 500 dona × $15, UZ → DE, sotuv €55 (QQSli, B2C, marketplace).

| Qadam | Natija |
|---|---|
| Product cost | $7,500 → EUR (as_of kurs bilan; kurs manbasi ko‘rsatiladi) |
| HS | 4202 21 nomzod (tashqi yuzasi charm). Material tasdiqlanmasa — `hs_confirmed=false`, ogohlantirish |
| Freight, insurance | **Foydalanuvchi kiritadi**; yo‘q bo‘lsa — “hisoblanmadi”, diapazon faqat manbali tarif bo‘lsa |
| Boj | TARIC seed: MFN va GSP+ variantlari yonma-yon |
| Import QQS | Ro‘yxatdan o‘tgan importyor → qaytariladi (sof xarajatga kirmaydi) |
| Sof tushum/dona | €55 / 1.19 = €46.22 |
| Marketplace fee | Foydalanuvchi kiritgan foiz × €55 |

Golden testlar: shu keys bir nechta qo‘lda hisoblangan kirish to‘plamlari bilan (Excel’da mustaqil hisoblanib, `tests/calc_engine/golden/*.json` ga yoziladi).

## 8. HS kod tavsiyasi

1. Mahsulot tavsifi → AI 1–3 nomzod (HS6) + har biri uchun ajratuvchi savollar (material, vazifa, tashqi yuza).
2. DB’dagi `hs_codes` bilan tekshirish (mavjud kodmi).
3. UI: “Tavsiya — yakuniy huquqiy tasnif emas. Bojxona brokeri yoki BTI/rasmiy organ orqali tasdiqlang.”
4. Foydalanuvchi tanlaydi → `hs_confirmed=true (user)`.
