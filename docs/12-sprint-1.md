# 12. Sprint 1 — Foundation + Calc Core (2 hafta)

## Holat (2026-11-17)

| Vazifa | Holat |
|---|---|
| A1 monorepo tuzilmasi, `.gitignore`, `.editorconfig`, README, `git init` | ✅ |
| A2 GitHub repo | ⏳ sizning akkauntingiz kerak |
| A3 CI (`.github/workflows/ci.yml`) | ✅ yozildi; backend qismi lokal o‘tdi, GitHub’da hali ishlamagan |
| A4 `.env.example` | ✅ api va web |
| A5 free tier qayta tekshiruvi | ⏳ |
| B2–B5 migratsiyalar, RLS, seed | ✅ yozildi, PostgreSQL parser bilan tekshirildi; real bazada **ishga tushirilmagan** |
| B1 Supabase loyihasi | ⏳ sizning akkauntingiz kerak |
| C1–C3 FastAPI: config, JWT, Problem Details, `/health`, `/me`, `/countries`, `/products` | ✅ 18 API testi (soxta repository bilan) |
| C4 OpenAPI → TS | ✅ `npm run gen:api` skripti (Node kerak) |
| C5 Render deploy | ⏳ |
| D1–D6 calc_engine | ✅ 35 test (golden + property), qamrov 98%, ruff + mypy strict toza |
| E1–E5 frontend | ✅ typecheck, 6 vitest testi, production build o‘tdi; brauzerda landing va `/app` → login yo‘naltirish tekshirildi |
| E6 Pages deploy | ⏳ |


**Maqsad:** Foydalanuvchi ro‘yxatdan o‘tib, kirib, dashboard’ni ko‘radi; `calc_engine` yadrosi golden testlardan o‘tadi.

## Vazifalar

### A. Repo va infratuzilma
- [ ] A1. `git init`, monorepo tuzilmasi: `apps/web`, `apps/api`, `supabase/`, `docs/`; `.gitignore`, `.editorconfig`, `README.md`
- [ ] A2. GitHub repo (private) + branch himoyasi (`main`)
- [ ] A3. GitHub Actions CI: web (eslint, tsc, vitest, build), api (ruff, mypy, pytest), gitleaks
- [ ] A4. `.env.example` (web va api), secret’lar ro‘yxati
- [ ] A5. Free tier limitlarini rasmiy sahifalarda qayta tekshirish → 11-hujjatni yangilash

### B. Database (Supabase)
- [ ] B1. Supabase dev loyihasi yaratish (siz tasdiqlaysiz — akkaunt sizniki)
- [ ] B2. Migratsiya 001: enumlar, `user_profiles` (+ trigger), `companies`, `products`, `product_categories`, `countries`, `data_sources`, `raw_data_records`, `normalized_data`, `analysis_jobs`
- [ ] B3. Migratsiya 002: `hs_codes`, `customs_tariffs`, `tax_rules`, `currency_rates`, `cost_calculations`
- [ ] B4. RLS siyosatlari + RLS testi (boshqa foydalanuvchi ma’lumotini o‘qib bo‘lmasligi)
- [ ] B5. Seed: `countries` (DE, AE, UZ), kategoriyalar (sumkalar, tekstil)

### C. Backend
- [ ] C1. FastAPI skeleti, `config.py`, structlog, Problem Details xatolari, CORS
- [ ] C2. JWT tekshiruvi (Supabase JWKS) + `get_current_user`
- [ ] C3. `/v1/health`, `/v1/me`, `/v1/countries`, `/v1/products` (CRUD)
- [ ] C4. OpenAPI → TS tiplar generatsiya skripti
- [ ] C5. Render’ga deploy (Free), health check

### D. calc_engine (eng muhim)
- [ ] D1. `Money` (Decimal + valyuta), `fx.convert` (kurs tashqaridan)
- [ ] D2. Incoterms matritsasi (EXW, FOB, CIF, DAP, DDP) + payer aniqlash
- [ ] D3. `CountryRulePack` protokoli + DE va AE rule pack’lar (stavkalar parametr sifatida, kodda emas)
- [ ] D4. `landed_cost()`, `profitability()` (revenue, margin, ROI, break-even, QQS qaytarilishi, QQSli narxdan sof tushum)
- [ ] D5. Golden testlar: Test keys 1 (3 ta Incoterm varianti, VAT registered ha/yo‘q), Test keys 2 (AE), chekka holatlar (contribution ≤ 0, quantity=0, valyuta aralash). Qiymatlar mustaqil Excel hisobida tekshirilgan
- [ ] D6. Property-based testlar (hypothesis): landed cost ≥ product cost; Incoterm o‘zgarsa umumiy zanjir xarajati o‘zgarmaydi, faqat taqsimot

### E. Frontend
- [ ] E1. Vite + React + TS + Tailwind + Router + TanStack Query + i18n (uz/en)
- [ ] E2. UI asos komponentlari (Button, Input, Card, Badge, Toast) + `DataValue`/`DataClassBadge` prototipi
- [ ] E3. Landing sahifa (PRD 10.1 bo‘limlari, asosiy xabar)
- [ ] E4. Auth sahifalari: Register, Login, Logout, Forgot/Reset password
- [ ] E5. AppLayout + Dashboard qobig‘i (kartalar; hali ishlamaydiganlari “tez orada”)
- [ ] E6. Cloudflare Pages’ga deploy

## Sprint 1 tugaganda tekshiruv (Definition of Done)
1. Yangi foydalanuvchi ro‘yxatdan o‘tadi, email tasdiqlaydi, kiradi, dashboard’ni ko‘radi — staging’da.
2. Boshqa foydalanuvchining mahsulotini API orqali ham, Supabase client orqali ham o‘qib bo‘lmaydi (test).
3. `calc_engine` testlari CI’da yashil; coverage ≥ 95%.
4. Hech qanday secret frontend bundle’da yo‘q (CI tekshiruvi).
5. Qisqa test hisoboti + demo.

## Sizdan kerak bo‘ladigan narsalar
- Supabase, Render, Cloudflare, GitHub akkauntlari (yoki ruxsat) — akkauntlarni siz yaratasiz/ulaysiz.
- Anthropic API kaliti (Sprint 2 dan; Sprint 1’da AI ishlatilmaydi).
- UN Comtrade bepul kaliti va eBay developer akkaunti (Sprint 3–4 uchun, oldindan ariza berish ma’qul).
- Google Trends API alpha’ga ariza (ixtiyoriy, uzoq kutish mumkin).
