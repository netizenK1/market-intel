# 04. Frontend Structure

## 1. Stack

React 18 + TypeScript (strict) · Vite · Tailwind CSS · React Router · TanStack Query (server state) · React Hook Form + Zod (formalar) · Recharts (grafiklar) · react-i18next (uz, en; ru keyin) · `@supabase/supabase-js` (faqat auth) · Vitest + Testing Library · Playwright (e2e, keyin).

UI komponentlar: o‘z kichik kutubxonamiz (Tailwind asosida, shadcn/ui uslubidagi nusxa komponentlar) — og‘ir UI framework yo‘q.

## 2. Papka tuzilmasi

```
apps/web/
├─ index.html
├─ vite.config.ts
├─ src/
│  ├─ main.tsx
│  ├─ app/
│  │  ├─ router.tsx            # marshrutlar, ProtectedRoute
│  │  ├─ providers.tsx         # QueryClient, i18n, AuthProvider
│  │  └─ layout/               # PublicLayout, AppLayout (sidebar + topbar)
│  ├─ pages/
│  │  ├─ landing/              # Hero, Features, HowItWorks, Markets, Samples, CTA, Footer
│  │  ├─ auth/                 # Login, Register, ForgotPassword, ResetPassword
│  │  ├─ dashboard/            # DashboardPage
│  │  ├─ analysis/             # NewAnalysisWizard, AnalysisStatus, AnalysisList
│  │  ├─ report/               # ReportPage + bo‘limlar
│  │  ├─ products/
│  │  ├─ calculator/           # Export/Import Calculator (AI’siz)
│  │  ├─ compare/
│  │  └─ settings/             # Profile, Company
│  ├─ features/                # domen logikasi + hooklar
│  │  ├─ auth/                 # useSession, supabase client
│  │  ├─ analyses/             # useCreateAnalysis, useAnalysisStatus (polling)
│  │  ├─ calc/
│  │  └─ products/
│  ├─ components/
│  │  ├─ ui/                   # Button, Input, Select, Card, Table, Tabs, Badge, Dialog, Toast, Skeleton
│  │  ├─ data/                 # DataValue, DataClassBadge, ConfidenceBadge, SourceTooltip, DataQualitySummary
│  │  └─ charts/               # PriceRangeChart, ScoreGauge, CostWaterfall, TrendLine
│  ├─ api/
│  │  ├─ client.ts             # fetch wrapper: token, Accept-Language, Problem Details → AppError
│  │  └─ schema.d.ts           # OpenAPI’dan generatsiya
│  ├─ i18n/
│  │  ├─ index.ts
│  │  └─ locales/{uz,en}/*.json
│  ├─ lib/                     # money formatlash (string → Intl.NumberFormat), sanalar
│  └─ styles/
└─ tests/
```

## 3. Muhim UI tamoyillari

- **`<DataValue dp={...} />`** — har bir raqam shu komponent orqali chiqadi: qiymat + birlik, rangli `DataClassBadge` (Verified / Observed / Estimated / User / **DEMO**), hover’da manba, sana, usul. Raqamni “yalang‘och” ko‘rsatish taqiqlanadi (lint qoidasi / code review).
- Estimated qiymatlar diapazon bilan (`€38–52`) ko‘rsatiladi.
- “Ma’lumot mavjud emas” holati — alohida `EmptyData` komponenti, sababi va “ma’lumot qo‘shish” tugmasi bilan.
- Har hisobot oxirida `DataQualitySummary` va `Sources & Methodology`.
- Mock rejimida butun sahifa tepasida doimiy ogohlantirish banneri.

## 4. Sahifalar va marshrutlar

| Yo‘l | Sahifa | Himoya |
|---|---|---|
| `/` | Landing | ochiq |
| `/login`, `/register`, `/forgot-password`, `/reset-password` | Auth | ochiq |
| `/app` | Dashboard (New Analysis, My Products, My Reports, Saved Markets, Recent, Compare, Calculator kartalari) | auth |
| `/app/analyses/new` | 3 qadamli wizard: Mahsulot → Bozor va biznes turi → Raqamlar (ixtiyoriy) | auth |
| `/app/analyses/:id` | Status (progress, bosqich) yoki `needs_input` savollari | auth |
| `/app/analyses/:id/report` | Hisobot (chap tomonda bo‘limlar navigatsiyasi) | auth |
| `/app/products` | | auth |
| `/app/calculator` | Landed cost kalkulyatori | auth |
| `/app/compare` | | auth |
| `/app/settings` | | auth |

## 5. Hisobot bo‘limlari (komponentlar)

ExecutiveSummary · MarketOverview · ConsumerAnalysis · CompetitorAnalysis (jadval PRD formatida) · MarketplaceAnalysis · ProductOpportunity (ScoreGauge ×3) · ImportExportRequirements · TaxesCustoms · Logistics · FinancialProjection (CostWaterfall + ssenariylar jadvali) · MarketingStrategy (har tavsiya PRD 12-bo‘lim formatida) · Risks · ActionPlan · SourcesMethodology.

## 6. Responsive

Mobil-first; dashboard sidebar < 1024px da drawer’ga aylanadi; jadvallar mobilda karta ko‘rinishiga o‘tadi; grafiklar `ResponsiveContainer`.

## 7. Hosting

Cloudflare Pages (static build, `npm run build` → `dist/`). SPA fallback: `_redirects` → `/* /index.html 200`. Env: faqat `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (bu ochiq kalit, RLS bilan himoyalangan), `VITE_API_BASE_URL`.
