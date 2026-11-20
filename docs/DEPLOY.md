# Bepul serverga chiqarish (deploy) — qadam-baqadam

Natija:
- **Sayt (frontend):** Cloudflare Pages — `https://market-intel.pages.dev` (bepul, uxlamaydi)
- **API (backend):** Render Free — `https://market-intel-api.onrender.com` (bepul, 15 daqiqa ishlatilmasa uxlaydi, birinchi so‘rovda ~1 daqiqada uyg‘onadi)
- **Baza + login:** Supabase Free — tayyor (`market-intel-dev`)

Hammasi bepul. Hech qayerga karta kiritish shart emas.

> ⚠️ Parollar va kalitlarni **chatga yozmang** — faqat shu yerda ko‘rsatilgan sayt maydonlariga kiriting.

---

## 1-qadam. GitHub — kodni internetga yuklash (5 daqiqa)

1. https://github.com ga kiring (akkaunt bo‘lmasa — **Sign up**).
2. O‘ng yuqoridagi **+** → **New repository**.
3. **Repository name:** `market-intel`
4. **Private** ni tanlang.
5. Pastdagi hech narsaga belgi qo‘ymang (README, .gitignore, license — **yo‘q**).
6. **Create repository** ni bosing.
7. Ochilgan sahifadagi manzilni nusxalang (`https://github.com/<login>/market-intel.git`) va **Claude’ga yuboring**.
8. Claude kodni yuklayotganda kompyuteringizda **GitHub login oynasi** chiqadi → **Sign in with your browser** → ruxsat bering.

## 2-qadam. Supabase — bazaning paroli (3 daqiqa)

1. https://supabase.com/dashboard → **market-intel-dev** loyihasi.
2. Chapda ⚙️ **Project Settings** → **Database** → **Reset database password**.
3. **Faqat harf va raqamlardan** iborat parol yozing (masalan 20 belgi). Parolni xavfsiz joyga yozib qo‘ying.
4. Yuqoridagi **Connect** tugmasi → **Transaction pooler** bo‘limidagi manzilni nusxalang. U shunday ko‘rinadi:
   `postgresql://postgres.qcpgmznxtnbqmsyazydw:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`
5. Notepad’ga qo‘yib, ikki joyni o‘zgartiring:
   - boshidagi `postgresql://` → `postgresql+asyncpg://`
   - `[YOUR-PASSWORD]` → sizning parolingiz (qavslarsiz)
6. Bu tayyor qatorni **4-qadamda** Render’ga kiritasiz. Chatga yozmang.

## 3-qadam. Cloudflare Pages — sayt (7 daqiqa)

1. https://dash.cloudflare.com → chapda **Workers & Pages** → **Create** → **Pages** tab → **Connect to Git**.
2. **GitHub**’ni ulang → `market-intel` repo’ni tanlang → **Begin setup**.
3. Sozlamalar:
   | Maydon | Qiymat |
   |---|---|
   | Project name | `market-intel` |
   | Production branch | `main` |
   | Framework preset | `None` |
   | Build command | `npm run build` |
   | Build output directory | `dist` |
   | Root directory (Advanced) | `apps/web` |
4. **Environment variables** (Advanced → Add variable) — bu qiymatlar ochiq, xavfsiz:
   | Nomi | Qiymat |
   |---|---|
   | `VITE_SUPABASE_URL` | `https://qcpgmznxtnbqmsyazydw.supabase.co` |
   | `VITE_SUPABASE_ANON_KEY` | `sb_publishable_w2P9tmZEqdcEKmNM-rsZfQ_FE9dWSS2` |
   | `VITE_API_BASE_URL` | `https://market-intel-api.onrender.com` |
   | `NODE_VERSION` | `20` |
5. **Save and Deploy**. 2–3 daqiqada sayt manzili chiqadi (masalan `https://market-intel.pages.dev`). **Manzilni Claude’ga yuboring.**

## 4-qadam. Render — API server (7 daqiqa)

1. https://render.com → **Get Started** → **GitHub orqali** ro‘yxatdan o‘ting.
2. **New +** → **Blueprint** → `market-intel` repo’ni tanlang (ko‘rinmasa: **Configure GitHub** → repo’ga ruxsat bering).
3. Render `render.yaml` faylini o‘qiydi va 2 ta maydonni so‘raydi:
   | Nomi | Qiymat |
   |---|---|
   | `DATABASE_URL` | 2-qadamdagi tayyor qator |
   | `CORS_ORIGINS` | 3-qadamdagi sayt manzili, masalan `https://market-intel.pages.dev` (oxirida `/` siz) |
4. **Apply** / **Deploy Blueprint**. 3–5 daqiqa kuting.
5. Servis manzili: `https://market-intel-api.onrender.com` (boshqacha bo‘lsa — **Claude’ga yuboring**, 3-qadamdagi `VITE_API_BASE_URL` ni o‘zgartiramiz).
6. Tekshiruv: brauzerda `https://market-intel-api.onrender.com/v1/health/ready` → `{"status":"ok",...}` chiqishi kerak.

## 5-qadam. Supabase — saytni login’ga tanitish (2 daqiqa)

1. Supabase → **market-intel-dev** → **Authentication** → **URL Configuration**.
2. **Site URL:** `https://market-intel.pages.dev` (3-qadamdagi manzil)
3. **Redirect URLs** → **Add URL**:
   - `https://market-intel.pages.dev/**`
   - `http://localhost:5173/**` (kompyuterda sinash uchun)
4. **Save**.

## 6-qadam. Sinov

1. Sayt manzilini oching → **Ro‘yxatdan o‘tish**.
2. Emailingizga kelgan xatdagi havolani bosing.
3. Kiring → Dashboard ochilishi kerak.
4. Muammo bo‘lsa — nima ko‘ringanini (yoki skrinshot) Claude’ga yuboring.

---

## Bepul tariflarning cheklovlari (bilib qo‘ying)

- **Render Free:** 15 daqiqa so‘rov bo‘lmasa uxlaydi; keyingi so‘rov ~1 daqiqa kutadi. Oyiga 750 soat.
- **Supabase Free:** 1 hafta umuman ishlatilmasa loyiha **pauza** qilinadi (ma’lumot o‘chmaydi, dashboard’dan **Restore** bosiladi). Login xatlari soatiga bir nechta bilan cheklangan.
- **Cloudflare Pages:** sayt uchun amalda cheklov yo‘q.

Keyinchalik real foydalanuvchilar ko‘paysa: Render Starter (~$7/oy) + Supabase Pro ($25/oy).
