# 10. MVP Development Roadmap

PRD 15-bo‘limidagi bosqichlar saqlandi, lekin **bitta o‘zgarish** bilan: hisoblash engine (PRD Phase 4) oldinga — Phase 1–2 ga ko‘chirildi. Sabablar: (1) PRD 16-bo‘limi uni asosiy farqlovchi qiymat deb ataydi; (2) u tashqi API’larga bog‘liq emas — darhol yozib, to‘liq test qilish mumkin; (3) AI hisobotlari unga tayanadi.

Sprint = 2 hafta. Muddatlar 1 nafar dasturchi + AI yordamchi uchun taxmin.

| Sprint | Bosqich | Natija (Definition of Done) |
|---|---|---|
| **S1** | Foundation + calc core | Repo, CI, web+api skeleti, Supabase sxemasi (asosiy jadvallar), auth (ro‘yxatdan o‘tish/kirish), landing, dashboard qobig‘i, `calc_engine` yadrosi + golden testlar (12-hujjat) |
| **S2** | Calculator MVP | DE/AE rule pack’lar, tarif/soliq seed (4202, tekstil), FX connectorlar (ECB, CBU), `/v1/calc/*`, Kalkulyator sahifasi (CostWaterfall, ssenariylar), HS tavsiya (AI + DB). **Test keys 1 hisob-kitobi qo‘lda tekshirilgan** |
| **S3** | Market Research MVP | Eurostat, Comtrade, World Bank connectorlari, job worker, `POST /v1/analyses` oqimi, Demand Index v1, Market Overview bo‘limi, Data Quality Summary |
| **S4** | Competitor & Marketplace | eBay Browse connector, web search → observed DataPoint’lar, raqobatchilar jadvali, narx diapazoni, Competition Index v1 |
| **S5** | AI Advisor | Synthesize + validator, marketing strategiya (PRD 12 format), 30 kunlik reja, risks, to‘liq hisobot sahifasi, uz/en |
| **S6** | Testing & Validation | 5–10 real tadbirkor bilan sinov, 2 test keys + 3 qo‘shimcha kategoriya, tariflarni rasmiy manbalar bilan solishtirish, xavfsizlik tekshiruvi, performance, xatolarni tuzatish |

Taxminan **12 hafta** ishlaydigan MVP’gacha.

## Priority xaritasi (PRD 16 ga moslangan)

| P0 (MVP) | P1 | P2 |
|---|---|---|
| Landing, Auth, Product input, Country selection | Etsy API, Keepa (budjet bo‘lsa) | Amazon SP-API (foydalanuvchi akkaunti) |
| **Landed cost + foyda kalkulyatori (DE, AE)** | Market comparison sahifasi | Real-time logistika API |
| **HS tavsiya + tekshirilgan tarif seed (MVP kategoriyalari)** | Ko‘proq HS kategoriyalari | PDF/Excel eksport |
| Market Research (trade stats, macro) | Google Trends (alpha tasdiqlansa) | Monitoring/alertlar |
| Raqobatchilar (eBay + web search signallari) | Admin tarif panelini kengaytirish | Monetizatsiya |
| AI Marketing Advisor | Ruscha til | Yangi mamlakatlar |
| Report page, provenance + confidence | | |

## Har sprint oxirida

- Demo + qisqa test hisoboti (nima ishlaydi, testlar natijasi, ma’lum muammolar) — PRD 20-bo‘lim, 17-band.
- `docs/` yangilanadi (o‘zgargan qarorlar).
