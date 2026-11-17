# 07. AI Agent Architecture

## 1. Yondashuv: “workflow”, erkin agent emas

PRD 9-bo‘limiga muvofiq MVP’da ko‘p agentli tizim yo‘q. Pipeline bosqichlarini **kod** boshqaradi; AI faqat aniq belgilangan 3 joyda ishlaydi. Bu arzonroq, bashorat qilinadigan va test qilinadigan.

```
intake (AI) → [needs_input?] → gather (kod) → score (kod) → calc (kod) → synthesize (AI) → validate (kod) → [repair (AI, 1 marta)]
```

| Bosqich | Kim | Kirish | Chiqish |
|---|---|---|---|
| **Intake** | AI (structured output) | Foydalanuvchi formasi | `ProductSpec` (kategoriya, material, HS nomzodlari + ishonch, yetishmayotgan maydonlar, savollar) |
| **Gather** | Kod | ProductSpec, mamlakatlar | `DataPoint[]` |
| **Score** | Kod | DataPoint[] | Demand/Competition/Opportunity (yoki “hisoblanmadi” + sabab) |
| **Calc** | calc_engine | Kirish + tarif + FX | `CalcResult` |
| **Synthesize** | AI (tool use + structured output) | DataPoint[], scores, CalcResult | Hisobot bo‘limlari JSON, tavsiyalar |
| **Validate** | Kod | Hisobot JSON | Xatolar ro‘yxati (raqam havolasiz, mavjud bo‘lmagan dp id, kafolat so‘zlari) |

## 2. Synthesize bosqichidagi tool’lar (faqat o‘qish/hisoblash)

| Tool | Vazifa |
|---|---|
| `get_data_points(metric_prefix, country)` | Mavjud DataPoint’larni olish |
| `run_scenario(price, quantity, channel)` | calc_engine orqali qo‘shimcha ssenariy (AI o‘zi hisoblamaydi) |
| `get_tariff(country, hs, origin)` | Tarif yozuvi + verifikatsiya holati |
| `web_search` (server tool, `allowed_domains` bilan cheklanmagan, lekin natija faqat `observed` + URL) | Raqobatchilar, narxlar, iste’molchi tadqiqotlari |

AI yozish/o‘chirish tool’lariga ega emas. Web search natijalari backend tomonidan `normalized_data` ga `observed` sifatida yoziladi, so‘ng AI ularga `dp` id orqali havola qiladi.

## 3. Raqam uydirilishiga qarshi himoya

1. Promptda qoida: matnda raqam faqat `{{dp:<id>}}` yoki `{{calc:<path>}}` placeholder orqali.
2. Validator: placeholder’dan tashqaridagi raqamlarni (yil va tartib raqamlaridan tashqari) topadi → `repair` bosqichi yoki bo‘limni “tekshirilmagan” deb belgilash.
3. Har bir tavsiyada `evidence_data_point_ids` bo‘sh bo‘lmasligi kerak.
4. Taqiqlangan iboralar ro‘yxati (“kafolatlanadi”, “aniq foyda” va h.k.) — validator ogohlantiradi.
5. Marketing budjeti va kutilgan natija — faqat diapazon, `estimated`.

## 4. Structured output sxemasi (qisqa)

```json
{
  "schema_version": "1.0",
  "locale": "uz",
  "sections": [
    {"key": "executive_summary", "body_md": "...{{dp:…}}...", "evidence": ["dp-id"], "confidence": "medium"}
  ],
  "recommendations": [
    {"kind": "strategy", "title": "...", "why": "...", "based_on": ["dp-id"],
     "steps": ["..."], "budget": {"min": "{{calc:…}}", "max": "…", "currency": "EUR"},
     "expected_outcome": "...", "risks": ["..."]}
  ],
  "missing_data": [{"what": "...", "why_it_matters": "...", "how_to_get": "..."}]
}
```

## 5. Til

- Hisobot `locale` (uz/en) da yoziladi. Ichki promptlar ingliz tilida (sifat va keshlash uchun barqaror), chiqish tili alohida ko‘rsatma bilan.
- O‘zbek tili sifati Sprint 2’da 10 ta namunaviy hisobot bilan qo‘lda baholanadi (atamalar lug‘ati: `i18n/glossary.uz.json` — “landed cost” = “yetkazib berilgan tannarx” va h.k.).

## 6. Model tanlovi

Model AI qatlamida bitta env (`AI_MODEL`) orqali almashtiriladi.

| Model | ID | Narx (1M token, kirish / chiqish) | Izoh |
|---|---|---|---|
| **Claude Opus 5.5** (tavsiya — default) | `claude-opus-5-5` | $4 / $20 | Eng yaxshi tahlil va strategiya sifati, tool use, structured output, 1M kontekst |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | $2 / $10 | Arzonroq muqobil |
| Claude Haiku 5.5 | `claude-haiku-5-5` | $0.10 / $0.50 | Juda arzon; Intake kabi oddiy bosqichlar uchun variant |

Texnik sozlamalar: adaptive thinking (default), `output_config.effort` (Intake — `low`, Synthesize — `medium`/`high`), streaming (uzun javoblar), prompt caching (tizim prompti + tool’lar barqaror prefiks), `refusal` stop reason uchun server-side `fallbacks: "default"`.

### Taxminiy xarajat (1 ta to‘liq hisobot, 2 mamlakat)

Taxmin: ~60K kirish + ~15K chiqish token (web search haqi alohida).

| Model | 1 hisobot | 100 hisobot/oy |
|---|---|---|
| Opus 5.5 | ≈ $0.24 + $0.30 ≈ **$0.55** | ≈ $55 |
| Sonnet 5.5 | ≈ $0.27 | ≈ $27 |
| Haiku 5.5 | ≈ $0.014 | ≈ $1.4 |

Bu **taxmin** — Sprint 2’da real token hisobi bilan yangilanadi (`ai_reports.input_tokens/output_tokens/cost_usd`). Keshlash kirish narxini sezilarli kamaytiradi.

> Model tanlovi va oylik budjet — sizning qaroringiz. Men default sifatida Opus 5.5 ni tavsiya qilaman; arzonroq model faqat siz tasdiqlasangiz qo‘yiladi. AI API umuman bo‘lmasa, `APP_ENV=demo` da mock javoblar ishlaydi (UI’da “DEMO” belgisi bilan).

## 7. Xarajat himoyasi

- `AI_MONTHLY_BUDGET_USD` — oshsa, yangi AI tahlillar to‘xtatiladi (kalkulyator ishlashda davom etadi).
- Foydalanuvchi bo‘yicha kunlik tahlil limiti (03-hujjat).
- Bir xil mahsulot × mamlakat × kun uchun gather natijalari keshlanadi.
