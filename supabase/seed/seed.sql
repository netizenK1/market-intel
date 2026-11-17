-- Seed: reference data only. No tariff/tax RATES are seeded here:
-- rates are added in Sprint 2 only after manual verification against official sources (URL + verified_at).

insert into public.countries (code, name_en, name_uz, currency, customs_union, is_enabled, rule_pack_version) values
  ('DE', 'Germany',              'Germaniya',             'EUR', 'EU',  true,  'de-1'),
  ('AE', 'United Arab Emirates', 'Birlashgan Arab Amirliklari', 'AED', 'GCC', true,  'ae-1'),
  ('UZ', 'Uzbekistan',           'O‘zbekiston',           'UZS', null,  false, null)
on conflict (code) do nothing;

insert into public.product_categories (slug, name_uz, name_en, default_hs_prefixes) values
  ('bags-leather-goods', 'Sumkalar va charm buyumlar', 'Bags & leather goods', '{4202}'),
  ('apparel-knitted',    'Trikotaj kiyimlar',          'Knitted apparel',      '{61}'),
  ('apparel-woven',      'To‘qima kiyimlar',           'Woven apparel',        '{62}'),
  ('home-textiles',      'Uy tekstili',                'Home textiles',        '{63}')
on conflict (slug) do nothing;

insert into public.data_sources (key, name, source_type, base_url, auth_type, env_secret_name, default_data_class, update_frequency, license_terms_url) values
  ('user_input',      'User input',                 'user',          null, null, null, 'user_provided', 'on demand', null),
  ('manual_seed',     'Manually verified reference', 'manual_seed',  null, null, null, 'verified',      'monthly review', null),
  ('ecb_fx',          'European Central Bank reference rates', 'official_api', 'https://data-api.ecb.europa.eu', 'none', null, 'verified', 'daily', 'https://www.ecb.europa.eu/home/disclaimer/html/index.en.html'),
  ('cbu_fx',          'Central Bank of Uzbekistan rates', 'official_api', 'https://cbu.uz', 'none', null, 'verified', 'daily', null),
  ('eurostat_comext', 'Eurostat Comext',           'official_api',  'https://ec.europa.eu/eurostat', 'none', null, 'verified', 'monthly', 'https://ec.europa.eu/eurostat/about-us/policies/copyright'),
  ('un_comtrade',     'UN Comtrade',               'official_api',  'https://comtradeapi.un.org', 'api_key', 'UN_COMTRADE_API_KEY', 'verified', 'monthly', 'https://comtradeplus.un.org'),
  ('world_bank',      'World Bank Open Data',      'official_api',  'https://api.worldbank.org/v2', 'none', null, 'verified', 'yearly', 'https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets'),
  ('ebay_browse',     'eBay Browse API',           'official_api',  'https://api.ebay.com/buy/browse/v1', 'oauth_client_credentials', 'EBAY_CLIENT_SECRET', 'observed', 'on demand', 'https://developer.ebay.com/join/api-license-agreement'),
  ('mock',            'Demo / mock data',          'mock',          null, null, null, 'mock', 'never', null)
on conflict (key) do nothing;
