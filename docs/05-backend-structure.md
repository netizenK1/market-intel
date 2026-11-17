# 05. Backend Structure

## 1. Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 (async) + asyncpg · Alembic **emas** — migratsiyalar Supabase CLI’da (yagona manba) · httpx (connectorlar) · tenacity (retry) · anthropic SDK · structlog (JSON log) · pytest + hypothesis (calc testlari) · ruff + mypy · uv (paket menejer).

### Nega FastAPI (PRD varianti) va nega Cloudflare Workers emas

- Hisob-kitob, ma’lumot qayta ishlash (pandas kerak bo‘lishi mumkin), AI SDK — Python ekotizimida eng qulay.
- Cloudflare Workers bepul tarifida so‘rov uchun CPU vaqti juda kichik (~10 ms) va Python Workers hali cheklangan — uzun AI tahlillari uchun mos emas. Workers keyinchalik faqat yengil vazifalar (masalan, cron trigger) uchun.
- Render Free FastAPI’ni Docker’siz ham ishga tushiradi; keyin Cloud Run/Fly’ga ko‘chirish oson (Dockerfile tayyorlanadi).

## 2. Papka tuzilmasi

```
apps/api/
├─ pyproject.toml
├─ Dockerfile
├─ app/
│  ├─ main.py                 # FastAPI app, middleware, router ulash, worker lifespan
│  ├─ config.py               # pydantic-settings: barcha env o‘zgaruvchilar
│  ├─ deps.py                 # get_db, get_current_user (JWT tekshiruvi)
│  ├─ errors.py               # AppError → Problem Details
│  ├─ api/v1/                 # routerlar: me, products, analyses, calc, logistics, compare, admin, health
│  ├─ schemas/                # Pydantic request/response modellar (API contract)
│  │  ├─ datapoint.py         # DataPoint, DataClass, Confidence
│  │  ├─ calc.py              # CalcInput, CostLine, CalcResult
│  │  └─ report.py            # ReportSection, Recommendation
│  ├─ db/
│  │  ├─ session.py
│  │  ├─ models.py            # SQLAlchemy modellar (migratsiyaga mos)
│  │  └─ repositories/        # har jadval guruhi uchun repo (owner_id filtri majburiy)
│  ├─ calc_engine/            # ⚠ AI’ga, DB’ga, tarmoqqa BOG‘LIQ EMAS — sof funksiyalar
│  │  ├─ money.py             # Money(Decimal, currency), yaxlitlash qoidalari
│  │  ├─ fx.py                # konvertatsiya (kurs tashqaridan beriladi)
│  │  ├─ incoterms.py         # xarajat segmentlari × kim to‘laydi matritsasi
│  │  ├─ landed_cost.py
│  │  ├─ profitability.py     # revenue, margin, ROI, break-even, ssenariylar
│  │  └─ countries/
│  │     ├─ base.py           # CountryRulePack protokoli
│  │     ├─ de.py             # EU/DE: customs value, import VAT bazasi
│  │     └─ ae.py             # GCC/AE
│  ├─ scoring/                # demand_index_v1, competition_index_v1, opportunity_v1
│  ├─ connectors/
│  │  ├─ base.py              # BaseConnector: rate limit, cache (raw_data_records), retry, normalize()
│  │  ├─ eurostat.py
│  │  ├─ un_comtrade.py
│  │  ├─ world_bank.py
│  │  ├─ fx_ecb.py, fx_cbu.py
│  │  ├─ ebay_browse.py
│  │  ├─ tariff_seed.py       # DB’dagi tekshirilgan tariflar
│  │  └─ mock.py              # faqat APP_ENV != production
│  ├─ services/               # modullar: market, consumer, competitor, marketplace, trade, logistics, finance, marketing
│  ├─ ai/
│  │  ├─ client.py            # Anthropic client, retry, token/cost hisoblash
│  │  ├─ orchestrator.py      # pipeline bosqichlari
│  │  ├─ tools.py             # AI chaqira oladigan tool’lar (faqat o‘qish/hisoblash)
│  │  ├─ prompts/             # versiyalangan promptlar (uz/en)
│  │  └─ validators.py        # AI javobidagi raqam/havolalarni tekshirish
│  └─ jobs/
│     ├─ worker.py            # navbatdan job olish (SKIP LOCKED), heartbeat, timeout
│     └─ pipeline.py          # intake → gather → score → calc → synthesize → validate
└─ tests/
   ├─ calc_engine/            # qo‘lda hisoblangan “golden” keyslar (PRD 17-bo‘lim)
   ├─ connectors/             # yozib olingan javoblar (fixtures), tarmoqsiz
   └─ api/
```

## 3. Job worker

- `main.py` lifespan’da 1–2 ta asyncio worker task ishga tushadi.
- `SELECT … FROM analysis_jobs WHERE status='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1`.
- Har bosqichdan keyin `stage`, `progress` yangilanadi; bosqich natijalari DB’ga yoziladi → server qayta ishga tushsa, job oxirgi tugallangan bosqichdan davom etadi (idempotent bosqichlar).
- `locked_at` 10 daqiqadan eski bo‘lsa — job “osilgan” deb qayta navbatga qo‘yiladi (max 3 urinish).
- Render Free uxlab qolishi: foydalanuvchi status sahifasida bo‘lganda polling trafik yaratadi va servisni uyg‘oq ushlab turadi. Server uxlab qolsa, keyingi so‘rovda job davom etadi.

## 4. Konfiguratsiya (env)

```
APP_ENV=development|demo|production
DATABASE_URL=postgresql+asyncpg://...      # Supabase pooler
SUPABASE_URL=...
SUPABASE_JWKS_URL=...
SUPABASE_SERVICE_ROLE_KEY=...              # faqat backend
ANTHROPIC_API_KEY=...
AI_MODEL=claude-opus-5-5
AI_MONTHLY_BUDGET_USD=...
UN_COMTRADE_API_KEY=...
EBAY_CLIENT_ID=... / EBAY_CLIENT_SECRET=...
CORS_ORIGINS=https://<pages-domain>
LOG_LEVEL=INFO
```

`.env.example` repoda, `.env` — `.gitignore` da.

## 5. Kod sifati qoidalari

- `calc_engine` va `scoring` — 100% branch coverage maqsadi; har formulaga golden test.
- Repository funksiyalari `owner_id` argumentisiz chaqirilmaydi (tip darajasida majburiy).
- Connector javoblari testlarda fixture’lardan o‘qiladi — CI tarmoqqa chiqmaydi.
- CI: GitHub Actions — ruff, mypy, pytest; web uchun eslint, tsc, vitest.
