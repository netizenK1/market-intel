-- 003: Row Level Security. Enabled on EVERY public table.
-- Backend uses its own connection and additionally filters by owner_id in code (defence in depth).

alter table public.countries          enable row level security;
alter table public.product_categories enable row level security;
alter table public.user_profiles      enable row level security;
alter table public.companies          enable row level security;
alter table public.products           enable row level security;
alter table public.data_sources       enable row level security;
alter table public.raw_data_records   enable row level security;
alter table public.analysis_jobs      enable row level security;
alter table public.normalized_data    enable row level security;
alter table public.hs_codes           enable row level security;
alter table public.customs_tariffs    enable row level security;
alter table public.tax_rules          enable row level security;
alter table public.currency_rates     enable row level security;
alter table public.cost_calculations  enable row level security;

-- ---------- reference data: read for signed-in users, write only via service_role ----------
create policy countries_read          on public.countries          for select to authenticated using (true);
create policy product_categories_read on public.product_categories for select to authenticated using (true);
create policy hs_codes_read           on public.hs_codes           for select to authenticated using (true);
create policy customs_tariffs_read    on public.customs_tariffs    for select to authenticated using (true);
create policy tax_rules_read          on public.tax_rules          for select to authenticated using (true);
create policy currency_rates_read     on public.currency_rates     for select to authenticated using (true);
-- countries are also needed on the public landing page
create policy countries_read_anon     on public.countries          for select to anon using (is_enabled);

-- data_sources, raw_data_records: no policies => closed to anon/authenticated (service_role bypasses RLS)

-- ---------- own profile ----------
create policy user_profiles_select_own on public.user_profiles for select to authenticated
  using (id = (select auth.uid()));
create policy user_profiles_update_own on public.user_profiles for update to authenticated
  using (id = (select auth.uid())) with check (id = (select auth.uid()));

-- ---------- owner-scoped tables ----------
create policy companies_owner on public.companies for all to authenticated
  using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));

create policy products_owner on public.products for all to authenticated
  using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));

create policy analysis_jobs_select_own on public.analysis_jobs for select to authenticated
  using (owner_id = (select auth.uid()));
-- jobs are created/updated by the backend only (status machine must not be forged by clients)

create policy cost_calculations_owner on public.cost_calculations for select to authenticated
  using (owner_id = (select auth.uid()));

-- normalized_data: global cache rows (analysis_job_id is null) are readable; job rows only by job owner
create policy normalized_data_read on public.normalized_data for select to authenticated
  using (
    analysis_job_id is null
    or exists (
      select 1 from public.analysis_jobs j
      where j.id = normalized_data.analysis_job_id and j.owner_id = (select auth.uid())
    )
  );
