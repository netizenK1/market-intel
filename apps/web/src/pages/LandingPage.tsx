import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { DataClassBadge } from "@/components/data/DataClassBadge";
import { Card } from "@/components/ui";

const FEATURE_KEYS = ["market", "competitors", "landed", "profit", "strategy", "honesty"] as const;

// Illustrative numbers from the engine's test fixture (docs/08 §7). Shown with the DEMO badge on purpose.
const SAMPLE_ROWS: Array<[string, string]> = [
  ["Unit landed cost", "€17.81"],
  ["Net price (excl. 19% VAT)", "€46.22"],
  ["Net margin", "26.1%"],
  ["Break-even", "139 pcs"],
];

export function LandingPage() {
  const { t } = useTranslation();
  const steps = t("landing.how", { returnObjects: true }) as string[];

  return (
    <>
      <section className="bg-gradient-to-b from-brand-50 to-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:py-24">
          <p className="text-sm font-medium uppercase tracking-wide text-brand-700">{t("landing.tagline")}</p>
          <h1 className="mt-4 max-w-3xl text-3xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            {t("landing.heroTitle")}
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-600">{t("landing.heroText")}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/register" className="rounded-lg bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-700">
              {t("landing.ctaStart")}
            </Link>
            <a href="#how" className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 hover:bg-slate-50">
              {t("landing.ctaHow")}
            </a>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="text-2xl font-semibold">{t("landing.purposeTitle")}</h2>
        <p className="mt-3 max-w-3xl text-slate-600">{t("landing.purposeText")}</p>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-14">
        <h2 className="text-2xl font-semibold">{t("landing.featuresTitle")}</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURE_KEYS.map((k) => (
            <Card key={k}>
              <h3 className="font-semibold">{t(`landing.features.${k}.title`)}</h3>
              <p className="mt-2 text-sm text-slate-600">{t(`landing.features.${k}.text`)}</p>
            </Card>
          ))}
        </div>
      </section>

      <section id="how" className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-14">
          <h2 className="text-2xl font-semibold">{t("landing.howTitle")}</h2>
          <ol className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s, i) => (
              <li key={s} className="rounded-xl bg-slate-50 p-5">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-600 text-sm font-bold text-white">
                  {i + 1}
                </span>
                <p className="mt-3 text-sm text-slate-700">{s}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-8 px-4 py-14 lg:grid-cols-2">
        <div>
          <h2 className="text-2xl font-semibold">{t("landing.marketsTitle")}</h2>
          <p className="mt-3 text-slate-600">{t("landing.marketsText")}</p>
          <div className="mt-4 flex gap-2">
            <span className="rounded-full bg-white px-3 py-1 text-sm ring-1 ring-slate-200">🇩🇪 Germany</span>
            <span className="rounded-full bg-white px-3 py-1 text-sm ring-1 ring-slate-200">🇦🇪 UAE</span>
          </div>
        </div>
        <Card>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">{t("landing.samplesTitle")}</h3>
            <DataClassBadge value="mock" />
          </div>
          <p className="mt-1 text-xs text-slate-500">Leather bags · UZ → DE · 500 pcs · {t("landing.sampleNote")}</p>
          <dl className="mt-4 divide-y divide-slate-100 text-sm">
            {SAMPLE_ROWS.map(([k, v]) => (
              <div key={k} className="flex justify-between py-2">
                <dt className="text-slate-600">{k}</dt>
                <dd className="font-medium tabular-nums">{v}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </section>

      <section className="bg-brand-900">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-4 px-4 py-12 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-xl font-semibold text-white">{t("landing.ctaFinalTitle")}</h2>
          <Link to="/register" className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-brand-900 hover:bg-brand-50">
            {t("landing.ctaStart")}
          </Link>
        </div>
      </section>
    </>
  );
}
