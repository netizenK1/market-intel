# 01. System Architecture

## 1. Yuqori darajadagi ko‘rinish

```
┌──────────────────────────┐        ┌───────────────────────────────────────────────┐
│  Browser (React SPA)     │  JWT   │  API (FastAPI, Python 3.12)                   │
│  Cloudflare Pages        ├───────►│  ┌────────────┐  ┌──────────────────────────┐ │
│  - Landing, Dashboard    │  REST  │  │ Routers    │  │ Job Worker (in-process)  │ │
│  - Analysis wizard       │◄───────┤  └─────┬──────┘  └───────────┬──────────────┘ │
│  - Report viewer         │        │        │                     │                │
└────────────┬─────────────┘        │  ┌─────▼─────────────────────▼─────────────┐  │
             │ Supabase Auth        │  │ Services                                │  │
             │ (login/register)     │  │  market · competitor · marketplace     │  │
             ▼                      │  │  trade (HS/tariff/tax) · logistics     │  │
┌──────────────────────────┐        │  │  finance · marketing · scoring         │  │
│ Supabase                 │◄───────┤  ├─────────────────────────────────────────┤  │
│ - Auth (JWT issuer)      │  SQL   │  │ calc_engine (pure Python, Decimal)      │  │
│ - PostgreSQL + RLS       │        │  │ country rule packs: DE, AE             │  │
└──────────────────────────┘        │  ├─────────────────────────────────────────┤  │
                                    │  │ AI Orchestrator (Claude API, tool use)  │  │
                                    │  ├─────────────────────────────────────────┤  │
                                    │  │ Connectors (adapters) + cache           │  │
                                    │  └───────┬─────────────────────────────────┘  │
                                    └──────────┼────────────────────────────────────┘
                                               ▼
              Eurostat · UN Comtrade · World Bank · ECB/CBU FX · eBay Browse API
              Claude web search (observed) · (P1) Keepa / data-provider · user input
```

## 2. Komponentlar

| Komponent | Texnologiya | Vazifa |
|---|---|---|
| Web client | React 18, TypeScript, Vite, Tailwind, React Router, TanStack Query, Recharts, react-i18next | UI, forma, hisobot, grafiklar. Hech qanday maxfiy kalit yo‘q. |
| Auth | Supabase Auth (email+parol, parolni tiklash) | JWT beradi. Backend JWT’ni JWKS orqali tekshiradi. |
| API | FastAPI + Pydantic v2 + SQLAlchemy 2 (async) / asyncpg | Barcha biznes logika, hisob-kitob, AI chaqiruvlari. |
| Job worker | Backend ichidagi asyncio worker, `analysis_jobs` jadvalidan `SELECT … FOR UPDATE SKIP LOCKED` | Uzun tahlillarni bajaradi (30–180 s). Keyinchalik alohida worker’ga ajratiladi. |
| calc_engine | Sof Python modul, `decimal.Decimal` | Landed cost, boj, QQS, foyda, ROI, break-even. AI’ga bog‘liq emas, 100% unit test. |
| Country rule packs | `countries/de.py`, `countries/ae.py` | Bojxona qiymati bazasi, QQS bazasi, stavka qidiruvi — har mamlakat uchun alohida. |
| Connectors | Har manba uchun adapter (`BaseConnector`) | Rate limit, retry, cache, `raw_data_records` ga yozish, normallashtirish. |
| AI Orchestrator | Anthropic Python SDK, tool use + structured output | So‘rovni tushunish, tool chaqirish, natijani tushuntirish, strategiya. |
| DB | Supabase PostgreSQL | Barcha ma’lumot, provenance, hisobotlar. RLS yoqilgan. |

## 3. Asosiy oqim: “New Market Analysis”

1. Foydalanuvchi forma to‘ldiradi → `POST /v1/analyses` → `analysis_jobs` (status `queued`) yaratiladi, `202 Accepted` + `job_id`.
2. Worker job’ni oladi → **Intake** (AI): mahsulotni aniqlash, kategoriya, HS nomzodlari, yetishmayotgan ma’lumotlar ro‘yxati.
3. Agar muhim ma’lumot yetishmasa → status `needs_input`, savollar `analysis_jobs.pending_questions` ga yoziladi. Frontend savollarni ko‘rsatadi → `POST /v1/analyses/{id}/answers`.
4. **Data gathering** (deterministik kod, AI emas): har maqsadli mamlakat uchun connectorlar parallel chaqiriladi (trade stats, macro, FX, marketplace, tariff seed).
5. **Scoring**: Demand/Competition/Opportunity index — deterministik formula (`scoring` servis), mavjud bo‘lmagan komponentlar vazni qayta normallashtiriladi.
6. **Calculation**: `calc_engine` landed cost va moliyaviy ssenariylarni hisoblaydi.
7. **Synthesis** (AI): barcha `DataPoint`lar va hisob natijalari AI’ga beriladi; AI hisobot bo‘limlarini (strukturalangan JSON) yozadi, har bir da’voda `data_point_id` havolasi bilan.
8. **Validation**: backend AI javobidagi har bir raqam/havola haqiqatan mavjud `DataPoint`ga mos kelishini tekshiradi (raqam “uydirilmasligi” uchun).
9. Hisobot `ai_reports` ga saqlanadi, status `completed`.

## 4. Arxitektura tamoyillari

- **AI hech qachon raqam ishlab chiqarmaydi**: raqamlar faqat connector yoki calc_engine’dan keladi. AI matni ichidagi raqamlar `{{dp:<uuid>}}` placeholder orqali render qilinadi.
- **Provenance majburiy**: `DataPoint` manbasiz saqlanmaydi (DB `CHECK` cheklovi).
- **Vaqtga bog‘liq qoidalar**: tarif/soliq yozuvlari `valid_from/valid_to` bilan; hisob-kitob `as_of_date` bilan bajariladi.
- **Kengaytiriluvchanlik**: yangi mamlakat = `countries` jadvalida yozuv + rule pack + seed tariflar + connector konfiguratsiyasi. Kod o‘zgarishi minimal.
- **Mock data**: faqat `APP_ENV=development|demo` da; `data_class='mock'` va UI’da qizil “DEMO DATA” belgisi. Production’da mock connector ro‘yxatdan o‘tkazilmaydi.

## 5. Muhitlar

| Muhit | Frontend | Backend | DB |
|---|---|---|---|
| local | `vite dev` (localhost:5173) | `uvicorn` (localhost:8000) | Supabase CLI local (Docker) yoki dev loyiha |
| staging/demo | Cloudflare Pages preview | Render Free | Supabase Free (dev loyiha) |
| production (keyin) | Cloudflare Pages | Render Starter yoki Cloud Run | Supabase Pro ($25/oy) |
