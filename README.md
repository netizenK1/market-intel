# AI Market & Trade Intelligence Platform (MVP)

Xorijiy bozorni o‘rganish, landed cost / foyda hisoblash va AI marketing strategiyasi platformasi. Birinchi bozorlar: Germaniya (DE), BAA (AE).

Loyiha hujjatlari: [docs/](docs/README.md).

## Tuzilma

```
apps/web     React + TypeScript + Vite + Tailwind (Cloudflare Pages)
apps/api     Python FastAPI (Render) — calc_engine, API, keyinchalik AI va connectorlar
supabase/    PostgreSQL migratsiyalari, RLS, seed
docs/        Arxitektura va rejalar
```

## Lokal ishga tushirish

### Backend

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/python -m uvicorn app.main:app --reload
```

`apps/api/.env.example` ni `.env` ga nusxalab, qiymatlarni to‘ldiring.

### Frontend (Node.js 20+ kerak)

```bash
cd apps/web
npm install
npm run dev
```

`apps/web/.env.example` ni `.env.local` ga nusxalang.

### Database

Supabase CLI bilan: `supabase db reset` (lokal) yoki `supabase db push` (dev loyiha). Migratsiyalar: `supabase/migrations/`.

## Muhim qoidalar

- Hisob-kitoblar faqat `apps/api/app/calc_engine` da (Decimal, AI’siz, testlar bilan).
- Har bir raqam manba, sana va ma’lumot turi (`verified | observed | estimated | user_provided | mock`) bilan saqlanadi.
- API kalitlari faqat backend env’da.
