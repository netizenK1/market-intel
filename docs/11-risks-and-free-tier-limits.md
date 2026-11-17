# 11. Texnik muammolar, bepul tariflarning real cheklovlari va eng arzon variant

> 2026-11-17 dagi qidiruv natijalari. Ko‘p raqamlar uchinchi tomon saytlaridan — **rasmiy narx sahifalarida qayta tekshirish** Sprint 1 vazifasi.

## 1. Bepul tariflar

| Xizmat | Bepul tarifda nima bor | Real cheklov / xavf | Xulosa |
|---|---|---|---|
| **Supabase Free** | ~500 MB DB, ~50K MAU, ~5 GB egress, 2 ta faol loyiha | **1 hafta faolsizlikdan keyin loyiha pauza qilinadi** (ma’lumot saqlanadi, qo‘lda tiklanadi); kafolatlangan backup yo‘q | MVP/demo uchun yetarli. Production — Pro **$25/oy** |
| **Render Free** (backend) | 750 instance-soat/oy | **15 daqiqa trafik bo‘lmasa uxlaydi**, uyg‘onish ~1 daqiqagacha; fayl tizimi vaqtinchalik; soatlar tugasa oy oxirigacha to‘xtatiladi; bepul Postgres 30 kunda o‘chadi (ishlatmaymiz) | Demo uchun mos. Doimiy ishlash: Starter (~$7/oy, narxni tekshirish) |
| **Cloudflare Pages** | Statik hosting, CDN | Oylik build soni cheklangan | Frontend uchun ideal |
| **Cloudflare Workers Free** | Kuniga ~100K so‘rov | So‘rov uchun CPU vaqti juda kichik; Python Workers cheklangan | Asosiy backend uchun **mos emas** |
| **GitHub** | Repo, Actions (private repo’da oylik daqiqa limiti) | — | CI + cron (FX yangilash, backup) |
| **UN Comtrade** | 500 chaqiruv/kun (rasmiy help center), 1 so‘rovda ≤ 500 qator (preview) | Kvota vaqtincha o‘zgartirilishi mumkin; ma’lumot kechikadi | Kesh bilan yetarli |
| **Google Trends** | Rasmiy API faqat alpha, ariza bilan | Tasdiq kafolatlanmagan; `pytrends` ishlamaydi | Demand Index’siz komponent bilan boshlaymiz |
| **Amazon** | PA-API 5 2026-yil aprel–mayda to‘xtatilgan, o‘rniga Creators API | Creators API affiliate **savdo talabiga** bog‘liq; raqobatchi sotuvi yo‘q | MVP’da Amazon API yo‘q |
| **AI API (Claude)** | Bepul emas | Har hisobot ≈ $0.01–0.55 (modelga qarab, 07-hujjat) | Budjet limiti bilan |

## 2. Asosiy texnik muammolar va yechimlar

| # | Muammo | Ta’sir | Yechim |
|---|---|---|---|
| 1 | **Raqobatchi sotuv hajmi ochiq emas** | PRD’dagi “sotuv” ustuni to‘ldirilmaydi | Signallar (sharhlar, reyting, listinglar); P1’da litsenziyalangan provider, `estimated/low` |
| 2 | **Amazon.ae / Noon uchun rasmiy API yo‘q** | BAA marketplace ma’lumoti kam | Web search (observed, URL bilan) + foydalanuvchi kiritgan listinglar; ishonchlilik `low/medium` |
| 3 | **EU TARIC uchun qulay rasmiy REST API yo‘q** | Tariflarni avtomatik olish qiyin | MVP’da qo‘lda tekshirilgan seed (URL + sana) + admin verifikatsiya; keyin TARIC fayllarini import qilish |
| 4 | **BAA tarifi rasmiy portallarda qidiruv interfeysi orqali** | Avtomatlashtirish qiyin | Seed; GCC tarifi ko‘p pozitsiyada bir xil bo‘lsa ham, har HS alohida tekshiriladi |
| 5 | **GSP+ (UZ → EU) preferensiyasi shartli** | Boj noto‘g‘ri bo‘lishi mumkin | MFN va GSP+ yonma-yon + kelib chiqish dalili (REX) ogohlantirishi |
| 6 | **B2C narxda QQS bor** | Tushum ~16% (DE) oshirib ko‘rsatilishi mumkin | Rule pack’da `price_includes_vat` majburiy maydon |
| 7 | **Ichki bozor hajmi** ko‘pincha ochiq emas | “Market size” bo‘sh qolishi | Import hajmi (verified) + “mavjud emas” halol ko‘rsatiladi |
| 8 | **Trade data kechikishi** (oylar/yil) | Eskirgan ko‘rinish | Davr doim ko‘rsatiladi |
| 9 | **AI javobi uzun (30–180 s)**, Render uxlashi | Timeout, yo‘qolgan job | DB navbat + idempotent bosqichlar + polling |
| 10 | **AI raqam uydirishi** | Ishonch yo‘qoladi | Placeholder + validator (07-hujjat) |
| 11 | **HS tasnif mas’uliyati** | Huquqiy xavf | Faqat “nomzod”, tasdiq foydalanuvchida, disclaimer |
| 12 | **Logistika narxlari ochiq emas** | Landed cost to‘liq emas | Foydalanuvchi taklifi; yo‘q bo‘lsa hisob “to‘liq emas” deb belgilanadi; manbasiz diapazon berilmaydi |
| 13 | **O‘zbek tilidagi AI sifati** | Atamalar noaniq | Lug‘at + qo‘lda baholash |
| 14 | **Supabase 500 MB** | Raw javoblar to‘ldiradi | Qisqartirib saqlash, TTL tozalash |
| 15 | **Litsenziyalar** (Comtrade, eBay, web kontent) | Saqlash/ko‘rsatish cheklovlari | `license_expires_at`, iqtibos qisqa, manba havolasi |

## 3. Eng kam xarajatli ishlaydigan variant

| Qism | Variant | Oylik xarajat |
|---|---|---|
| Frontend | Cloudflare Pages | $0 |
| Backend | Render Free (demo) | $0 |
| DB + Auth | Supabase Free | $0 |
| Trade/macro/FX ma’lumotlari | Eurostat, Comtrade (free key), World Bank, ECB, CBU | $0 |
| Marketplace | eBay Browse API + web search | $0 + web search haqi |
| AI | Claude API | ~$1–55 / 100 hisobot (modelga qarab) |
| **Jami (demo/pilot)** | | **≈ $0 + AI ishlatilishi** |

**Pilot foydalanuvchilar bilan barqaror ishlash uchun tavsiya:** Render Starter + Supabase Pro ≈ **$32/oy** + AI. Supabase pauzasi va Render uxlashi real foydalanuvchilar oldida yomon tajriba beradi.

## Manbalar (qidiruv)

- Supabase: https://www.jetadmin.io/blog/supabase-pricing-2026-guide-to-plans-limits-and-real-world-costs/ , https://automationatlas.io/answers/supabase-free-tier-limits-2026/
- Render: https://render.com/docs/free
- UN Comtrade: https://comtradewiki.azurewebsites.net/?p=78
- Google Trends API alpha: https://ppc.land/google-opens-alpha-testing-for-new-trends-api-targeting-developers-and-journalists/ , https://www.seroundtable.com/google-trends-api-applications-approvals-39978.html
- Amazon PA-API → Creators API: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation
