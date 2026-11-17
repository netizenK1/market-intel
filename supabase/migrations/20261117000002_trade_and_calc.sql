-- 002: HS codes, tariffs, tax rules, FX, cost calculations
-- Rates are NEVER hard-coded in application code: they live here with source URL and validity dates.

create table public.hs_codes (
  code           text not null check (code ~ '^[0-9]{4,12}$'),
  nomenclature   text not null check (nomenclature in ('HS6','CN8','TARIC10','AE_HS12','HS4')),
  country_code   char(2) references public.countries(code),   -- null for global HS
  description_en text not null,
  description_uz text,
  parent_code    text,
  valid_from     date not null default date '1900-01-01',
  valid_to       date,
  primary key (code, nomenclature, valid_from)
);
create index hs_codes_code_prefix_idx on public.hs_codes(code text_pattern_ops);

create table public.customs_tariffs (
  id                  uuid primary key default gen_random_uuid(),
  importing_country   char(2) not null references public.countries(code),
  customs_union       text,
  hs_code             text not null,
  nomenclature        text not null,
  origin_country      char(2) references public.countries(code),      -- null = erga omnes
  preference_regime   text not null check (preference_regime in ('MFN','GSP','GSP_PLUS','EBA','FTA','OTHER')),
  duty_type           text not null default 'ad_valorem' check (duty_type in ('ad_valorem','specific','mixed')),
  ad_valorem_rate     numeric(9,6) check (ad_valorem_rate >= 0 and ad_valorem_rate <= 10),
  specific_amount     numeric(18,4),
  specific_unit       text,
  conditions          text,
  valid_from          date not null,
  valid_to            date,
  source_url          text not null,
  verified_at         timestamptz,
  verified_by         uuid references auth.users(id),
  verification_status text not null default 'unverified'
                        check (verification_status in ('verified','unverified','expired')),
  created_at          timestamptz not null default now(),
  constraint customs_tariffs_valid_order check (valid_to is null or valid_from <= valid_to),
  constraint customs_tariffs_verified_has_date check (verification_status <> 'verified' or verified_at is not null)
);
create index customs_tariffs_lookup_idx
  on public.customs_tariffs(importing_country, hs_code, origin_country, valid_from desc);

create table public.tax_rules (
  id                  uuid primary key default gen_random_uuid(),
  country_code        char(2) not null references public.countries(code),
  tax_type            text not null check (tax_type in ('import_vat','vat','excise','customs_fee','other')),
  rate                numeric(9,6) check (rate >= 0 and rate <= 10),
  base_formula_key    text,
  applies_to          jsonb not null default '{}',
  recoverable_if      jsonb not null default '{}',
  de_minimis_amount   numeric(18,4),
  valid_from          date not null,
  valid_to            date,
  source_url          text not null,
  verified_at         timestamptz,
  verified_by         uuid references auth.users(id),
  verification_status text not null default 'unverified'
                        check (verification_status in ('verified','unverified','expired')),
  created_at          timestamptz not null default now(),
  constraint tax_rules_valid_order check (valid_to is null or valid_from <= valid_to),
  constraint tax_rules_verified_has_date check (verification_status <> 'verified' or verified_at is not null)
);
create index tax_rules_lookup_idx on public.tax_rules(country_code, tax_type, valid_from desc);

create table public.currency_rates (
  base       char(3) not null,
  quote      char(3) not null,
  rate_date  date not null,
  rate       numeric(18,8) not null check (rate > 0),
  source_id  uuid not null references public.data_sources(id),
  source_url text not null,
  created_at timestamptz not null default now(),
  primary key (base, quote, rate_date, source_id)
);

create table public.cost_calculations (
  id               uuid primary key default gen_random_uuid(),
  owner_id         uuid not null default auth.uid() references auth.users(id) on delete cascade,
  analysis_job_id  uuid references public.analysis_jobs(id) on delete cascade,
  product_id       uuid references public.products(id) on delete set null,
  input            jsonb not null,
  result           jsonb not null,
  engine_version   text not null,
  as_of_date       date not null,
  tariff_ids       uuid[] not null default '{}',
  tax_rule_ids     uuid[] not null default '{}',
  created_at       timestamptz not null default now()
);
create index cost_calculations_owner_idx on public.cost_calculations(owner_id, created_at desc);
