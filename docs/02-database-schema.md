# 02. Database Schema (Supabase PostgreSQL)

## 1. Umumiy qoidalar

- PK: `id uuid default gen_random_uuid()` (lookup jadvallarda tabiiy kalit: `countries.code`, `currencies`).
- Har jadvalda `created_at timestamptz default now()`, o‘zgaradiganlarida `updated_at` (trigger).
- Pul: `numeric(18,4)` + alohida `currency char(3)`. Hech qachon `float`.
- Foiz/stavka: `numeric(9,6)` (masalan `0.190000` = 19%).
- Foydalanuvchiga tegishli jadvallarda `owner_id uuid references auth.users` + RLS.
- Global ma’lumotnoma jadvallari (tariflar, soliq qoidalari, FX) — hamma o‘qiydi, faqat `service_role`/admin yozadi.

### Enum turlari

```sql
create type data_class  as enum ('verified','observed','estimated','user_provided','mock');
create type confidence  as enum ('high','medium','low','none');
create type job_status  as enum ('queued','running','needs_input','completed','failed','cancelled');
create type trade_flow  as enum ('export','import');
create type business_type as enum ('manufacturer_exporter','importer_reseller','marketplace_seller','service','other');
create type incoterm    as enum ('EXW','FCA','FOB','CFR','CIF','CPT','CIP','DAP','DPU','DDP');
create type transport_mode as enum ('road','air','sea','rail','multimodal');
```

> PRD’da 3 sinf (verified/observed/estimated) bor. Men 2 ta qo‘shdim: `user_provided` (foydalanuvchi kiritgan narx, transport taklifi) va `mock` (demo). Bu PRD’ning 11- va 20-bo‘limlari talabini bajarish uchun kerak.

## 2. Provenance modeli (eng muhim qism)

Har bir ko‘rsatkich `normalized_data` jadvalida **DataPoint** sifatida saqlanadi:

```sql
create table normalized_data (
  id            uuid primary key default gen_random_uuid(),
  metric_key    text not null,          -- 'trade.import_value', 'price.listing', 'macro.gdp_per_capita' ...
  country_code  char(2) references countries(code),
  hs_code       text,                   -- ixtiyoriy
  subject       jsonb,                  -- {"partner":"UZ","year":2024,"listing_id":"..."}
  value_numeric numeric(20,6),
  value_text    text,
  unit          text not null,          -- 'EUR','USD','kg','%','index','count'
  period_start  date, period_end date,  -- ma’lumot qaysi davrga tegishli
  data_class    data_class not null,
  confidence    confidence not null,
  method        text not null,          -- 'api:eurostat/comext', 'calc:demand_index_v1', 'user_input'
  source_id     uuid references data_sources(id),
  source_url    text,
  retrieved_at  timestamptz not null,
  raw_record_id uuid references raw_data_records(id),
  analysis_job_id uuid references analysis_jobs(id) on delete cascade, -- null = global kesh
  created_at    timestamptz default now(),
  constraint chk_source check (data_class in ('user_provided','estimated') or source_url is not null),
  constraint chk_value  check (value_numeric is not null or value_text is not null)
);
create index on normalized_data (metric_key, country_code, hs_code);
create index on normalized_data (analysis_job_id);
```

`estimated` qiymatlar uchun `method` formulaning versiyasini ko‘rsatadi va `subject.inputs` ichida kirish DataPoint id’lari saqlanadi (izlanuvchanlik).

## 3. Jadvallar

### A. Foydalanuvchi va kompaniya

| # | Jadval | Asosiy ustunlar | Izoh |
|---|---|---|---|
| 1 | `users` | — | Supabase `auth.users` ishlatiladi; alohida jadval yaratilmaydi. |
| 2 | `user_profiles` | `id (=auth.users.id) PK`, `full_name`, `locale ('uz'\|'en')`, `home_country char(2)`, `role ('user'\|'admin')` | Trigger orqali ro‘yxatdan o‘tganda yaratiladi. |
| 3 | `companies` | `id`, `owner_id`, `name`, `country_code`, `is_vat_registered bool`, `vat_country_codes char(2)[]`, `business_type` | Soliq maqomi hisob-kitobga ta’sir qiladi (import QQS qaytarilishi). |
| 4 | `products` | `id`, `owner_id`, `company_id`, `name`, `description`, `category_id`, `origin_country char(2)`, `material`, `unit_weight_kg`, `unit_volume_m3`, `unit_cost numeric`, `unit_cost_currency`, `attributes jsonb` | |
| 5 | `product_categories` | `id`, `parent_id`, `slug`, `name_uz`, `name_en`, `default_hs_prefixes text[]` | Ierarxik. |

### B. Geografiya va bozor

| # | Jadval | Asosiy ustunlar | Izoh |
|---|---|---|---|
| 6 | `countries` | `code char(2) PK`, `name_en`, `name_uz`, `currency char(3)`, `customs_union ('EU'\|'GCC'\|'EAEU'\|null)`, `is_enabled bool`, `rule_pack_version` | Faqat `is_enabled` mamlakatlar UI’da ko‘rinadi. |
| 7 | `markets` | `id`, `country_code`, `category_id`, `name`, `notes` | Mamlakat × kategoriya. |
| 8 | `market_research` | `id`, `analysis_job_id`, `market_id`, `summary jsonb`, `data_point_ids uuid[]` | Modul 1 natijasi. |
| 9 | `consumer_segments` | `id`, `analysis_job_id`, `country_code`, `segment ('budget'\|'middle'\|'premium'\|…)`, `description`, `evidence_data_point_ids uuid[]`, `confidence` | Dalilsiz segment saqlanmaydi (`array_length(evidence…) > 0` CHECK). |

### C. Raqobat va marketplace

| # | Jadval | Asosiy ustunlar |
|---|---|---|
| 10 | `competitors` | `id`, `country_code`, `brand_name`, `website`, `origin_country`, `first_seen_at`, `source_url` |
| 11 | `competitor_products` | `id`, `competitor_id`, `name`, `category_id`, `attributes jsonb`, `source_url` |
| 12 | `marketplace_listings` | `id`, `marketplace ('ebay_de','amazon_de','amazon_ae','noon_ae','etsy',…)`, `external_id`, `country_code`, `title`, `price numeric`, `currency`, `price_includes_vat bool`, `rating numeric(3,2)`, `review_count int`, `seller_name`, `url`, `observed_at`, `data_class`, `source_id`, `competitor_product_id null`, `license_expires_at` | UNIQUE(`marketplace`,`external_id`,`observed_at::date`). `license_expires_at` — manba shartlari ma’lumotni qancha saqlashga ruxsat bersa. |

### D. Ma’lumot manbalari

| # | Jadval | Asosiy ustunlar |
|---|---|---|
| 13 | `data_sources` | `id`, `key ('eurostat_comext','un_comtrade',…) UNIQUE`, `name`, `source_type ('official_api'\|'licensed_api'\|'open_page'\|'user'\|'ai_web_search'\|'manual_seed'\|'mock')`, `base_url`, `auth_type`, `env_secret_name` (kalitning **nomi**, qiymati emas), `usage_limits jsonb`, `update_frequency`, `license_terms_url`, `license_notes`, `default_data_class`, `last_success_at`, `last_error_at`, `quality_status ('ok'\|'degraded'\|'down'\|'disabled')`, `is_enabled` |
| 14 | `raw_data_records` | `id`, `source_id`, `request_fingerprint` (hash), `request_params jsonb`, `response_body jsonb` yoki `response_ref` (katta bo‘lsa Storage), `http_status`, `fetched_at`, `expires_at` | Kesh + audit. Saqlash muddati: 90 kun (litsenziya ruxsat bergan qisqaroq bo‘lsa — o‘sha). |
| 15 | `normalized_data` | yuqoriga qarang | |

### E. Savdo, soliq, logistika

| # | Jadval | Asosiy ustunlar | Izoh |
|---|---|---|---|
| 16 | `hs_codes` | `code text` (6–10 xona), `nomenclature ('HS6'\|'CN8'\|'TARIC10'\|'AE_HS12')`, `country_code null` (HS6 global), `description_en`, `parent_code`, `valid_from`, `valid_to` | PK (`code`,`nomenclature`,`valid_from`). |
| 17 | `customs_tariffs` | `id`, `importing_country`, `customs_union`, `hs_code`, `nomenclature`, `origin_country null`, `preference_regime ('MFN'\|'GSP'\|'GSP_PLUS'\|'FTA'\|…)`, `duty_type ('ad_valorem'\|'specific'\|'mixed')`, `ad_valorem_rate numeric(9,6)`, `specific_amount`, `specific_unit`, `conditions text` (masalan, “REX kelib chiqish dalili kerak”), `valid_from`, `valid_to`, `source_url NOT NULL`, `verified_at`, `verified_by`, `verification_status ('verified'\|'unverified'\|'expired')` | `unverified` stavka hisobda “tasdiqlanmagan” deb ko‘rsatiladi. |
| 18 | `tax_rules` | `id`, `country_code`, `tax_type ('import_vat'\|'vat'\|'excise'\|'customs_fee'\|…)`, `rate`, `base_formula_key` (rule pack’dagi funksiya nomi), `applies_to jsonb` (HS prefikslari, shaxs turi), `recoverable_if jsonb` (masalan `{"vat_registered":true}`), `de_minimis_amount`, `valid_from`, `valid_to`, `source_url NOT NULL`, `verified_at`, `verification_status` | |
| 19 | `logistics_rates` | `id`, `owner_id null` (null = umumiy), `origin_country`, `dest_country`, `mode`, `incoterm`, `price_basis ('per_kg'\|'per_cbm'\|'per_container'\|'flat')`, `amount`, `currency`, `min_charge`, `transit_days_min/max`, `valid_from/to`, `data_class`, `source_url`, `quote_reference` | Foydalanuvchi kiritgan taklif — `owner_id` bilan, faqat o‘ziga ko‘rinadi. |
| 20 | `certifications` | `id`, `country_code`, `hs_prefix`, `name` (masalan “REACH”, “GPSR”, “ECAS/ESMA”), `mandatory bool`, `description`, `authority`, `source_url`, `verified_at` | |
| 21 | `currency_rates` | `base char(3)`, `quote char(3)`, `rate_date date`, `rate numeric(18,8)`, `source_id`, `source_url`, PK(`base`,`quote`,`rate_date`,`source_id`) | ECB, CBU (O‘zbekiston MB), CBUAE. |

### F. Hisob-kitob, ballar, AI

| # | Jadval | Asosiy ustunlar |
|---|---|---|
| 22 | `cost_calculations` | `id`, `owner_id`, `analysis_job_id null`, `product_id`, `input jsonb` (to‘liq `CalcInput`), `result jsonb` (to‘liq `CalcResult` — har qator bilan), `engine_version`, `as_of_date`, `fx_rate_ids`, `tariff_ids uuid[]`, `tax_rule_ids uuid[]` | Qayta hisoblash mumkin bo‘lishi uchun barcha kirishlar saqlanadi. |
| 23 | `market_scores` | `id`, `analysis_job_id`, `country_code`, `score_type ('demand'\|'competition'\|'opportunity')`, `value numeric(5,2) null`, `formula_version`, `components jsonb` (har komponent: qiymat, vazn, data_point_id), `confidence`, `not_computed_reason` |
| 24 | `ai_reports` | `id`, `owner_id`, `analysis_job_id UNIQUE`, `locale`, `sections jsonb`, `data_quality_summary jsonb`, `model`, `prompt_version`, `input_tokens`, `output_tokens`, `cost_usd`, `validation_errors jsonb` |
| 25 | `ai_recommendations` | `id`, `report_id`, `kind ('strategy'\|'pricing'\|'channel'\|'launch_30d'\|'risk')`, `title`, `rationale`, `evidence_data_point_ids uuid[]`, `steps jsonb`, `budget_estimate jsonb` (har doim diapazon + `data_class='estimated'`), `expected_outcome`, `risks` |
| 26 | `analysis_jobs` | `id`, `owner_id`, `product_id`, `target_countries char(2)[]`, `request jsonb`, `status job_status`, `stage text`, `progress smallint`, `pending_questions jsonb`, `answers jsonb`, `error jsonb`, `attempts int`, `locked_at`, `locked_by`, `started_at`, `finished_at` | Index: (`status`,`created_at`) worker uchun. |
| 27 | `user_feedback` | `id`, `owner_id`, `report_id`, `section_key`, `rating smallint`, `comment` |

Qo‘shimcha (tavsiya): `saved_markets` (`owner_id`, `country_code`, `category_id`) — dashboard’dagi “Saved Markets” uchun; `audit_log` — admin tarif o‘zgarishlari uchun.

## 4. Bog‘lanishlar (asosiy)

```
auth.users 1─1 user_profiles
auth.users 1─* companies 1─* products *─1 product_categories
products 1─* analysis_jobs 1─1 ai_reports 1─* ai_recommendations
analysis_jobs 1─* normalized_data, market_scores, consumer_segments, market_research, cost_calculations
data_sources 1─* raw_data_records 1─* normalized_data
countries 1─* customs_tariffs, tax_rules, certifications, markets
competitors 1─* competitor_products 1─* marketplace_listings
```

## 5. Row Level Security

- Foydalanuvchi jadvallari (`companies`, `products`, `analysis_jobs`, `ai_reports`, `ai_recommendations`, `cost_calculations`, `user_feedback`, `saved_markets`, foydalanuvchi `logistics_rates`): `using (owner_id = auth.uid())` — select/insert/update/delete.
- Bolalik jadvallari (`market_scores`, `consumer_segments`, `market_research`, job’ga bog‘liq `normalized_data`): `exists (select 1 from analysis_jobs j where j.id = analysis_job_id and j.owner_id = auth.uid())`.
- Ma’lumotnoma jadvallari (`countries`, `hs_codes`, `customs_tariffs`, `tax_rules`, `certifications`, `currency_rates`, `product_categories`): `select` — `authenticated`; yozish — faqat `service_role`.
- `data_sources`, `raw_data_records`: frontendga umuman yopiq (faqat backend `service_role`).

> Backend asosan o‘z DB ulanishi orqali ishlaydi, lekin foydalanuvchi so‘rovlarida `owner_id` filtri **kodda ham** qo‘llanadi (RLS — ikkinchi himoya qatlami).

## 6. Saqlash muddatlari (MVP)

| Ma’lumot | Muddat |
|---|---|
| `raw_data_records` | 90 kun yoki litsenziya muddati (qaysi qisqa bo‘lsa) |
| `marketplace_listings` | manba shartlariga ko‘ra (`license_expires_at`), default 30 kun |
| `analysis_jobs`, `ai_reports` | foydalanuvchi o‘chirguncha |
| `currency_rates`, `customs_tariffs`, `tax_rules` | doimiy (tarix kerak — eski hisobotlarni qayta tiklash uchun) |

Supabase Free 500 MB — shuning uchun katta javoblar `raw_data_records` da siqilgan/qisqartirilgan holda saqlanadi, kunlik cron eski yozuvlarni tozalaydi.

## 7. Migratsiyalar

`supabase/migrations/*.sql` — Supabase CLI orqali. Seed: `supabase/seed/` (mamlakatlar, kategoriyalar, MVP HS kodlari, tekshirilgan tarif/soliq yozuvlari manba URL bilan).
