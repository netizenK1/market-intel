-- 001: core types, users/profiles, companies, products, reference geography, data provenance, jobs
-- See docs/02-database-schema.md

-- gen_random_uuid() is built into PostgreSQL 13+, no extension needed.
-- All functions pin search_path to '' and use schema-qualified names (Supabase security advisor).

-- ---------- enums ----------
create type public.data_class as enum ('verified','observed','estimated','user_provided','mock');
create type public.confidence as enum ('high','medium','low','none');
create type public.job_status as enum ('queued','running','needs_input','completed','failed','cancelled');
create type public.business_type as enum ('manufacturer_exporter','importer_reseller','marketplace_seller','service','other');
create type public.incoterm as enum ('EXW','FCA','FOB','CFR','CIF','CPT','CIP','DAP','DPU','DDP');
create type public.transport_mode as enum ('road','air','sea','rail','multimodal');
create type public.user_role as enum ('user','admin');

-- ---------- helpers ----------
create or replace function public.set_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at := pg_catalog.now();
  return new;
end;
$$;

-- ---------- reference: countries & categories ----------
create table public.countries (
  code              char(2) primary key,
  name_en           text not null,
  name_uz           text not null,
  currency          char(3) not null,
  customs_union     text check (customs_union in ('EU','GCC','EAEU')),
  is_enabled        boolean not null default false,
  rule_pack_version text,
  created_at        timestamptz not null default now()
);

create table public.product_categories (
  id                  uuid primary key default gen_random_uuid(),
  parent_id           uuid references public.product_categories(id) on delete restrict,
  slug                text not null unique,
  name_uz             text not null,
  name_en             text not null,
  default_hs_prefixes text[] not null default '{}',
  created_at          timestamptz not null default now()
);

-- ---------- users ----------
create table public.user_profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  full_name    text,
  locale       text not null default 'uz' check (locale in ('uz','en','ru')),
  home_country char(2) references public.countries(code),
  role         public.user_role not null default 'user',
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create trigger trg_user_profiles_updated before update on public.user_profiles
  for each row execute function public.set_updated_at();

-- create a profile automatically for every new auth user
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.user_profiles (id, full_name, locale)
  values (
    new.id,
    new.raw_user_meta_data ->> 'full_name',
    coalesce(nullif(new.raw_user_meta_data ->> 'locale', ''), 'uz')
  );
  return new;
end;
$$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();
revoke execute on function public.handle_new_user() from public, anon, authenticated;

-- users must not be able to promote themselves to admin
create or replace function public.prevent_role_change() returns trigger
language plpgsql set search_path = '' as $$
begin
  if new.role is distinct from old.role and current_user = 'authenticated' then
    raise exception 'role cannot be changed by the user';
  end if;
  return new;
end;
$$;
create trigger trg_user_profiles_role before update on public.user_profiles
  for each row execute function public.prevent_role_change();

create table public.companies (
  id                uuid primary key default gen_random_uuid(),
  owner_id          uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name              text not null check (char_length(name) between 1 and 200),
  country_code      char(2) references public.countries(code),
  business_type     public.business_type not null default 'other',
  is_vat_registered boolean not null default false,
  vat_country_codes char(2)[] not null default '{}',
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index companies_owner_idx on public.companies(owner_id);
create trigger trg_companies_updated before update on public.companies
  for each row execute function public.set_updated_at();

create table public.products (
  id                 uuid primary key default gen_random_uuid(),
  owner_id           uuid not null default auth.uid() references auth.users(id) on delete cascade,
  company_id         uuid references public.companies(id) on delete set null,
  name               text not null check (char_length(name) between 1 and 200),
  description        text check (char_length(description) <= 4000),
  category_id        uuid references public.product_categories(id),
  origin_country     char(2) references public.countries(code),
  material           text,
  unit_weight_kg     numeric(12,4) check (unit_weight_kg >= 0),
  unit_volume_m3     numeric(12,6) check (unit_volume_m3 >= 0),
  unit_cost          numeric(18,4) check (unit_cost >= 0),
  unit_cost_currency char(3),
  attributes         jsonb not null default '{}',
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  constraint products_cost_currency check (unit_cost is null or unit_cost_currency is not null)
);
create index products_owner_idx on public.products(owner_id, created_at desc);
create trigger trg_products_updated before update on public.products
  for each row execute function public.set_updated_at();

-- ---------- data provenance ----------
create table public.data_sources (
  id                 uuid primary key default gen_random_uuid(),
  key                text not null unique,
  name               text not null,
  source_type        text not null check (source_type in
                       ('official_api','licensed_api','open_page','user','ai_web_search','manual_seed','mock')),
  base_url           text,
  auth_type          text,
  env_secret_name    text,           -- NAME of the env var holding the key; never the key itself
  usage_limits       jsonb not null default '{}',
  update_frequency   text,
  license_terms_url  text,
  license_notes      text,
  default_data_class public.data_class not null,
  last_success_at    timestamptz,
  last_error_at      timestamptz,
  quality_status     text not null default 'ok' check (quality_status in ('ok','degraded','down','disabled')),
  is_enabled         boolean not null default true,
  created_at         timestamptz not null default now()
);

create table public.raw_data_records (
  id                  uuid primary key default gen_random_uuid(),
  source_id           uuid not null references public.data_sources(id) on delete cascade,
  request_fingerprint text not null,
  request_params      jsonb not null default '{}',
  response_body       jsonb,
  response_ref        text,
  http_status         int,
  fetched_at          timestamptz not null default now(),
  expires_at          timestamptz not null
);
create index raw_data_records_lookup_idx on public.raw_data_records(source_id, request_fingerprint, fetched_at desc);
create index raw_data_records_expiry_idx on public.raw_data_records(expires_at);

create table public.analysis_jobs (
  id                uuid primary key default gen_random_uuid(),
  owner_id          uuid not null default auth.uid() references auth.users(id) on delete cascade,
  product_id        uuid references public.products(id) on delete set null,
  target_countries  char(2)[] not null,
  request           jsonb not null,
  status            public.job_status not null default 'queued',
  stage             text,
  progress          smallint not null default 0 check (progress between 0 and 100),
  pending_questions jsonb,
  answers           jsonb,
  error             jsonb,
  attempts          int not null default 0,
  locked_at         timestamptz,
  locked_by         text,
  started_at        timestamptz,
  finished_at       timestamptz,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index analysis_jobs_queue_idx on public.analysis_jobs(status, created_at);
create index analysis_jobs_owner_idx on public.analysis_jobs(owner_id, created_at desc);
create trigger trg_analysis_jobs_updated before update on public.analysis_jobs
  for each row execute function public.set_updated_at();

create table public.normalized_data (
  id              uuid primary key default gen_random_uuid(),
  metric_key      text not null,
  country_code    char(2) references public.countries(code),
  hs_code         text,
  subject         jsonb not null default '{}',
  value_numeric   numeric(20,6),
  value_text      text,
  unit            text not null,
  period_start    date,
  period_end      date,
  data_class      public.data_class not null,
  confidence      public.confidence not null,
  method          text not null,
  source_id       uuid references public.data_sources(id),
  source_url      text,
  retrieved_at    timestamptz not null,
  raw_record_id   uuid references public.raw_data_records(id) on delete set null,
  analysis_job_id uuid references public.analysis_jobs(id) on delete cascade,
  created_at      timestamptz not null default now(),
  -- every non-user, non-estimated value must point to a source
  constraint normalized_data_source_required
    check (data_class in ('user_provided','estimated') or source_url is not null),
  constraint normalized_data_value_required
    check (value_numeric is not null or value_text is not null),
  constraint normalized_data_period_order
    check (period_start is null or period_end is null or period_start <= period_end)
);
create index normalized_data_metric_idx on public.normalized_data(metric_key, country_code, hs_code);
create index normalized_data_job_idx on public.normalized_data(analysis_job_id);
