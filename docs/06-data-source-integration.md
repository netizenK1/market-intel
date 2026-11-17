# 06. Data Source Integration Plan

> Holatlar 2026-11-17 dagi qidiruvga asoslangan. Har bir manba integratsiyadan oldin rasmiy sahifada qayta tekshiriladi (Sprint vazifasi). “Tekshirilmagan” deb belgilangan narsalar fakt sifatida qabul qilinmasin.

## 1. Manbalar jadvali

| Manba | Nima beradi | Kirish | Narx / limit | MVP holati | data_class |
|---|---|---|---|---|---|
| **Eurostat Comext** (API / SDMX) | EU (DE) importi: hamkor mamlakat × CN8 kod × oy/yil, qiymat (EUR) va hajm (kg) | Ochiq REST, kalitsiz | Bepul | **P0** — DE uchun asosiy trade data | verified |
| **Eurostat** (boshqa datasetlar) | Aholi, uy xo‘jaligi iste’moli, onlayn xarid ulushi | Ochiq | Bepul | P0 | verified |
| **UN Comtrade** | Global trade (AE importlari, UZ eksportlari, mirror data), HS6 | API kalit (Developer Portal) | Bepul individual kalit: **500 chaqiruv/kun** (rasmiy help center; o‘zgarishi mumkin) | **P0** — AE uchun asosiy | verified |
| **World Bank Open Data** | YaIM aholi jon boshiga, aholi, PPP | Ochiq REST, kalitsiz | Bepul | P0 | verified |
| **ECB reference rates** | EUR kurslari | Ochiq (SDMX/XML) | Bepul | P0 | verified |
| **O‘zbekiston MB (CBU)** | UZS kurslari | Ochiq JSON | Bepul | P0 | verified |
| **CBUAE** | AED (USD’ga 3.6725 peg) | Ochiq sahifa | Bepul | P0 | verified |
| **eBay Browse API** | Listinglar: narx, holat, sotuvchi, (ba’zan) sotilgan soni — eBay.de | OAuth (developer account) | Bepul, kunlik limit bilan (tekshirish kerak) | **P0** — DE marketplace signal | observed |
| **Claude web search** (server tool) | Ochiq sahifalardan narxlar, brendlar, sharhlar, hisobotlar — **URL bilan** | Anthropic API | Qidiruv uchun alohida haq (tekshirish kerak) | **P0** — boshqa API yo‘q joylarda (Amazon.ae, Noon, brendlar) | observed (manba URL majburiy) |
| **Foydalanuvchi kiritgani** | Tannarx, transport taklifi, o‘z listinglari | UI | — | P0 | user_provided |
| **Tariflar seed** (Access2Markets / TARIC / BAA rasmiy manbalari) | Boj stavkalari, QQS, shartlar | Qo‘lda tekshirilib DB’ga kiritiladi | — | **P0** — MVP kategoriyalari uchun | verified (agar `verified_at` bor) |
| **Amazon Creators API** (PA-API 5 o‘rnini bosgan) | Mahsulot ma’lumotlari | Associates akkaunti + sotuv talabi | Bepul, lekin **affiliate savdolar bo‘lmasa kirish to‘xtatiladi** | P2 — MVP uchun real emas | observed |
| **Amazon SP-API** | Faqat **sotuvchining o‘z** akkaunti ma’lumotlari | Seller account | — | P2 — foydalanuvchi o‘z akkauntini ulasa | verified (o‘ziniki) |
| **Etsy Open API v3** | Listinglar | API kalit, ilova tasdig‘i | Bepul | P1 | observed |
| **Noon** | Ochiq ommaviy product API topilmadi | — | — | Faqat web search orqali | observed |
| **Keepa** (yoki shunga o‘xshash litsenziyalangan provider) | Amazon narx tarixi, sotuv reytingi (BSR) — sotuv **taxmini** uchun | API kalit | Pullik (oylik obuna; narxni tekshirish kerak) | **P1, budjet tasdiqlansa** | observed / estimated |
| **Google Trends** | Qidiruv qiziqishi | Rasmiy API faqat **alpha**, ariza orqali; norasmiy `pytrends` ishlamaydi/ToS xavfi | — | **Ariza topshiriladi**; tasdiqlanmaguncha Demand Index’dan chiqariladi (vazn qayta normallashtiriladi) | verified (agar rasmiy API) |
| **WTO Tariff data** | MFN o‘rtacha tariflar | Ochiq | Bepul | P1 — tekshiruv (cross-check) uchun | verified |

## 2. Muhim cheklovlar va qarorlar

1. **Raqobatchilarning aniq sotuv hajmi** — hech bir bepul rasmiy manbada yo‘q. MVP’da ko‘rsatilmaydi; o‘rniga “signal”lar: sharhlar soni, reyting, listinglar soni, narx zichligi. Sotuv taxmini faqat P1’da litsenziyalangan provider bilan va `estimated, confidence=low` sifatida.
2. **Scraping yo‘q.** Amazon/Noon sahifalari to‘g‘ridan-to‘g‘ri skrep qilinmaydi. Web search tool natijalari — ochiq sahifalar, URL bilan, `observed`.
3. **Trade data kechikishi**: Comtrade/Comext ma’lumotlari odatda 2–18 oy kechikadi. UI’da davr (`period`) doim ko‘rsatiladi.
4. **HS darajasi**: Comtrade — HS6; Comext — CN8; tariflar — TARIC 10 xona (EU), BAA — 8–12 xona. Mapping `hs_codes.parent_code` orqali.
5. **Bozor hajmi**: to‘g‘ridan-to‘g‘ri “ichki bozor hajmi” bepul manbada ko‘pincha yo‘q. MVP: **import hajmi** (verified) + ishlab chiqarish/iste’mol proksi (bor bo‘lsa). “Market size” sifatida faqat manbali raqam; aks holda “mavjud emas” + import hajmi ko‘rsatiladi.

## 3. Connector shartnomasi (`BaseConnector`)

```python
class BaseConnector(Protocol):
    key: str                                  # data_sources.key
    async def fetch(self, params: dict) -> RawRecord          # tarmoq, retry, rate limit
    def normalize(self, raw: RawRecord) -> list[DataPoint]    # sof funksiya, test qilinadi
```

- Har chaqiruvdan oldin kesh: `raw_data_records.request_fingerprint` + `expires_at`.
- Comtrade uchun kunlik budjet hisoblagichi (500 dan oshmaslik, 20% zaxira).
- Xatolik → `data_sources.quality_status='degraded'`, hisobot shu manbasiz davom etadi va Data Quality Summary’da ko‘rsatiladi.

## 4. Yangilanish jadvali

| Ma’lumot | Chastota | Mexanizm |
|---|---|---|
| FX (ECB, CBU) | kunlik | GitHub Actions cron → `/v1/admin/...refresh` (yoki Supabase pg_cron) |
| Trade stats | talab bo‘yicha + 30 kun kesh | job ichida |
| Tariflar/soliq | qo‘lda, oyiga 1 marta tekshiruv | admin panel, `verified_at` |
| Listinglar | talab bo‘yicha, 7 kun kesh | job ichida |

## 5. MVP seed qamrovi (tariflar)

Faqat test keyslar uchun tekshirilgan yozuvlar:
- **HS 4202** (sumkalar; 4202 21 — tashqi yuzasi charmdan) → DE (EU TARIC: MFN va GSP+ — O‘zbekiston GSP+ benefitsiari, kelib chiqish dalili/REX talabi bilan) va AE (GCC umumiy tarifi).
- **HS 61–63** (tekstil, MVP uchun 3–5 ta keng tarqalgan pozitsiya) → AE va DE.
- Soliqlar: DE import QQS / QQS (standart va kamaytirilgan), AE QQS.

Har yozuv: rasmiy URL, tekshirilgan sana, kim tekshirgan. Yozuvlarsiz HS uchun hisobot “tarif tasdiqlanmagan — broker bilan tekshiring” deydi va foydalanuvchiga stavkani o‘zi kiritish imkonini beradi (`user_provided`).
