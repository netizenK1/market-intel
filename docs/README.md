# AI Market & Trade Intelligence Platform — Texnik hujjatlar (v0.1, draft)

**Holat:** Tasdiqlash uchun. Kod yozilmagan (PRD 20.1-bandiga muvofiq).
**Sana:** 2026-11-17
**Birinchi bozorlar:** Germaniya (DE), BAA (AE). Kelib chiqish mamlakati (MVP test): O‘zbekiston (UZ).

## Hujjatlar

| # | Hujjat | Mazmuni |
|---|---|---|
| 01 | [System Architecture](01-system-architecture.md) | Umumiy arxitektura, komponentlar, ma’lumot oqimi |
| 02 | [Database Schema](02-database-schema.md) | 27+ jadval, provenance modeli, RLS |
| 03 | [API Architecture](03-api-architecture.md) | REST contract, endpointlar, xatolar formati |
| 04 | [Frontend Structure](04-frontend-structure.md) | React/Vite tuzilmasi, sahifalar, i18n |
| 05 | [Backend Structure](05-backend-structure.md) | FastAPI tuzilmasi, servislar, job runner |
| 06 | [Data Source Integration Plan](06-data-source-integration.md) | Har bir manba: holati, limiti, litsenziyasi |
| 07 | [AI Agent Architecture](07-ai-agent-architecture.md) | Orchestrator, tool’lar, model tanlovi, xarajat |
| 08 | [Import/Export Calculation Logic](08-calculation-logic.md) | Landed cost, boj, QQS, Incoterms, foyda formulalari |
| 09 | [Security Plan](09-security-plan.md) | Auth, RLS, secrets, rate limit, loglar |
| 10 | [MVP Development Roadmap](10-mvp-roadmap.md) | Bosqichlar (qayta tartiblangan) |
| 11 | [Texnik muammolar va bepul tarif cheklovlari](11-risks-and-free-tier-limits.md) | Real cheklovlar, xavflar, eng arzon variant |
| 12 | [Sprint 1](12-sprint-1.md) | Birinchi sprint uchun aniq vazifalar |

## Asosiy qarorlar (qisqacha)

1. **Monorepo**: `apps/web` (React+TS+Vite+Tailwind) + `apps/api` (Python FastAPI) + `supabase/` (migratsiyalar).
2. **Hisob-kitoblar AI’dan to‘liq mustaqil**: `calc_engine` — sof Python, `Decimal`, unit testlar bilan. AI faqat natijani tushuntiradi.
3. **Har bir raqam = `DataPoint`**: qiymat + birlik/valyuta + manba URL + sana + usul + ishonchlilik + sinf (`verified | observed | estimated | user_provided | mock`).
4. **Soliq/tarif qoidalari mamlakat bo‘yicha alohida “rule pack”** (`countries/de.py`, `countries/ae.py`), amal qilish sanasi bilan. Bir mamlakat qoidasi boshqasiga qo‘llanmaydi.
5. **Uzun tahlillar — asinxron job** (DB’dagi `analysis_jobs` jadvali + worker). Frontend statusni so‘rab turadi.
6. **Marketplace ma’lumotlari** — faqat rasmiy API (eBay Browse API), litsenziyalangan provider (P1, pullik) va ochiq sahifalar ustidan AI web search (manba bilan, `observed`). Scraping yo‘q.
7. **Tariflar MVP’da qo‘lda tekshirilgan “seed” jadvaldan** (TARIC/Access2Markets va BAA rasmiy manbalaridan URL + tekshirilgan sana bilan). Avtomatik TARIC API yo‘q (11-hujjatga qarang).

## Tasdiqlash kerak bo‘lgan qarorlar

1. Backend hosting: **Render Free** (bepul, lekin 15 daqiqadan keyin uxlaydi) yoki **~$7/oy** doimiy instance.
2. AI model va oylik AI budjeti (07-hujjat, 7-bo‘lim).
3. Pullik marketplace data-provider (masalan, Keepa) ga budjet ajratiladimi — P1 uchun.
4. Repository shu papkada (`YAXYO`) `git init` qilinadimi va GitHub’ga yuklanadimi.
