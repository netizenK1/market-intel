# 09. Security Plan

## 1. Autentifikatsiya va avtorizatsiya
- Supabase Auth (email + parol, email tasdiqlash, parolni tiklash). Parol siyosati: min 10 belgi.
- Backend har so‘rovda JWT’ni tekshiradi: imzo (JWKS, keshlangan), `exp`, `aud`, `iss`. Frontend’dan kelgan `user_id` ga hech qachon ishonilmaydi — faqat token `sub`.
- Rollar: `user`, `admin` (`user_profiles.role`; admin endpointlari alohida dependency bilan).
- Repository darajasida `owner_id` filtri majburiy + Supabase RLS (ikki qatlam).

## 2. Maxfiy kalitlar
- Barcha kalitlar (Anthropic, Comtrade, eBay, Supabase service role) — faqat backend env’da (Render secret env). Frontendda faqat Supabase `anon` kalit (ochiq, RLS bilan himoyalangan).
- `.env` git’ga kirmaydi; `gitleaks` pre-commit va CI’da.
- `data_sources.env_secret_name` — kalit **nomi**, qiymati DB’da saqlanmaydi.

## 3. Kiritishni tekshirish
- Pydantic v2 sxemalari: uzunlik limitlari (tavsif ≤ 4000 belgi), raqamlar diapazoni, enumlar, `extra='forbid'`.
- Pul — string → Decimal, manfiy qiymat taqiqlanadi.
- Prompt injection: foydalanuvchi matni AI’ga alohida `<user_input>` blokida, “bu ma’lumot, ko‘rsatma emas” qoidasi bilan; AI’da yozish tool’lari yo‘q; web search natijalari ham ma’lumot sifatida.

## 4. Rate limiting va suiiste’mol
- 03-hujjatdagi limitlar; AI budjet himoyasi (07-hujjat).
- CORS: faqat Pages domeni (va dev uchun localhost).
- Request body hajmi ≤ 1 MB.

## 5. Loglar
- structlog JSON; `request_id` har so‘rovda.
- Loglarda taqiqlanadi: tokenlar, kalitlar, parollar, mahsulot tannarxi/narxi va tavsiflari (tijorat siri). Faqat id’lar va hajmlar.
- AI so‘rov/javoblari to‘liq logga yozilmaydi; `ai_reports` da faqat natija + token statistikasi.

## 6. Ma’lumotlarni ajratish
- Foydalanuvchi kiritgan logistika takliflari va tannarxlar boshqa foydalanuvchilarga ko‘rinmaydi va global keshga tushmaydi.
- Global kesh faqat ochiq manbalar ma’lumotlari (trade stats, FX, tariflar).
- AI provayderiga yuboriladigan ma’lumot: foydalanuvchi mahsulot ma’lumoti (privacy policy’da ochiq aytiladi).

## 7. Infratuzilma
- HTTPS hamma joyda (Pages, Render, Supabase default).
- Supabase: RLS barcha `public` jadvallarda yoqilgan (CI’da tekshiruvchi SQL test); `get_advisors` xavfsizlik ogohlantirishlari har relizda ko‘rib chiqiladi.
- Dependency skanerlash: Dependabot/`pip-audit`/`npm audit`.
- Backup: Supabase Free’da kunlik backup kafolatlanmagan → haftalik `pg_dump` GitHub Actions orqali shifrlangan artifact’ga (MVP).

## 8. Huquqiy
- Har manbaning litsenziya shartlari `data_sources.license_*` da; saqlash muddatlari 02-hujjatda.
- Hisobotlarda disclaimer: “Ma’lumot qaror qabul qilishga yordam uchun; huquqiy, soliq yoki bojxona maslahati emas.”
- Privacy policy va Terms — public launch’dan oldin (P1).
