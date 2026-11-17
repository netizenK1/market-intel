# 03. API Architecture

## 1. Umumiy

- Base URL: `/v1`. JSON. OpenAPI avtomatik (`/docs` faqat dev’da ochiq).
- Auth: `Authorization: Bearer <Supabase access token>`. Backend JWT’ni Supabase JWKS orqali tekshiradi (`aud=authenticated`, `exp`, `iss`).
- OpenAPI’dan frontend TypeScript tiplari generatsiya qilinadi (`openapi-typescript`) — **API contract yagona manbadan**.
- Pul: JSON’da **string** (`"1234.5600"`) + `currency` — float xatolaridan saqlanish uchun.

### Yagona `DataPoint` formati (har bir raqam shu ko‘rinishda qaytadi)

```json
{
  "id": "6f1c…",
  "metric": "trade.import_value",
  "value": "18234000.00",
  "unit": "EUR",
  "period": {"start": "2024-01-01", "end": "2024-12-31"},
  "data_class": "verified",
  "confidence": "high",
  "method": "api:eurostat/comext DS-045409",
  "source": {"name": "Eurostat Comext", "url": "https://…"},
  "retrieved_at": "2026-11-17T09:12:00Z"
}
```

### Xatolar formati (RFC 9457 Problem Details)

```json
{
  "type": "https://docs.<domain>/errors/hs-code-ambiguous",
  "title": "HS code aniqlanmadi",
  "status": 422,
  "detail": "Mahsulot materiali ko‘rsatilmagan: charm, sun’iy charm yoki to‘qimachilik?",
  "code": "HS_CODE_AMBIGUOUS",
  "fields": {"material": "required"},
  "request_id": "req_…"
}
```

`detail` foydalanuvchi tilida (`Accept-Language: uz|en`).

## 2. Endpointlar

### Profil
| Metod | Yo‘l | Tavsif |
|---|---|---|
| GET | `/v1/me` | Profil + kompaniyalar |
| PATCH | `/v1/me` | Til, ism, mamlakat |
| POST/GET/PATCH | `/v1/companies[/{id}]` | Kompaniya (QQS maqomi bilan) |

### Ma’lumotnomalar (ochiq, autentifikatsiya bilan)
| GET | `/v1/countries` | Faqat yoqilgan mamlakatlar |
| GET | `/v1/categories` | Kategoriya daraxti |
| GET | `/v1/hs-codes/search?q=&country=` | Matn bo‘yicha qidiruv (DB) |

### Mahsulotlar
| GET/POST | `/v1/products` | Ro‘yxat / yaratish |
| GET/PATCH/DELETE | `/v1/products/{id}` | |

### Tahlil (asosiy oqim)
| Metod | Yo‘l | Tavsif |
|---|---|---|
| POST | `/v1/analyses` | Yangi tahlil. Body: `product` (yoki `product_id`), `target_countries[]`, `business_type`, `quantity`, `unit_cost`, `planned_price`, `incoterm?`, `notes`. Javob: `202 {job_id, status}` |
| GET | `/v1/analyses` | Ro‘yxat (Recent analyses) |
| GET | `/v1/analyses/{id}` | Status: `stage`, `progress`, `pending_questions` |
| POST | `/v1/analyses/{id}/answers` | `needs_input` savollariga javob → job qayta navbatga |
| POST | `/v1/analyses/{id}/cancel` | |
| GET | `/v1/analyses/{id}/report` | To‘liq hisobot: bo‘limlar + `data_points[]` + `scores` + `calculation` + `data_quality_summary` + `sources[]` |
| POST | `/v1/analyses/{id}/feedback` | Bo‘lim bo‘yicha baho |

Polling: frontend `GET /v1/analyses/{id}` ni 3 s oralig‘ida (status `completed/failed/needs_input` bo‘lguncha) chaqiradi. Keyinchalik SSE.

### Kalkulyator (AI’siz, sinxron, tez)
| Metod | Yo‘l | Tavsif |
|---|---|---|
| POST | `/v1/calc/hs-suggest` | Mahsulot tavsifi → HS nomzodlari (AI + DB), har biri `confidence` va `questions` bilan. **Hech qachon yakuniy tasnif emas.** |
| POST | `/v1/calc/landed-cost` | `CalcInput` → `CalcResult` (08-hujjat). Deterministik. |
| POST | `/v1/calc/scenarios` | Bir nechta narx/miqdor ssenariysi |
| GET | `/v1/calc/tariff?country=DE&hs=420221&origin=UZ&date=` | Topilgan tarif yozuvi(lari) + verifikatsiya holati |
| GET | `/v1/fx?base=USD&quote=EUR&date=` | Kurs + manba |

### Logistika
| GET/POST/DELETE | `/v1/logistics/quotes` | Foydalanuvchi transport takliflari |

### Taqqoslash
| POST | `/v1/compare` | Bir mahsulot, 2+ mamlakat — mavjud hisobotlardan yig‘ma jadval |

### Admin (role=admin)
| GET/POST/PATCH | `/v1/admin/tariffs`, `/v1/admin/tax-rules` | Tarif/soliq yozuvlarini kiritish va **verify** qilish |
| GET | `/v1/admin/data-sources` | Manbalar holati, oxirgi yangilanish |
| POST | `/v1/admin/data-sources/{key}/refresh` | Qo‘lda yangilash |

### Tizim
| GET | `/v1/health` | Liveness (Render uchun) |
| GET | `/v1/health/ready` | DB + manbalar holati |

## 3. Rate limiting

- Foydalanuvchi bo‘yicha: `POST /v1/analyses` — 10/kun (Free), umumiy API — 60/daqiqa.
- IP bo‘yicha (auth’siz endpointlar): 30/daqiqa.
- MVP’da Postgres asosidagi sliding window (`rate_limits` jadvali) yoki `slowapi` in-memory (bitta instance bo‘lgani uchun yetarli).

## 4. Versiyalash

- `/v1` ichida faqat qo‘shimcha (backward-compatible) o‘zgarishlar. Breaking — `/v2`.
- Hisobot JSON’ida `schema_version` maydoni.
