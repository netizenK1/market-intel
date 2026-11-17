import { useTranslation } from "react-i18next";
import { setLocale, SUPPORTED_LOCALES, type Locale } from "@/i18n";

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  return (
    <label className="inline-flex items-center gap-1.5 text-sm text-slate-600">
      <span className="sr-only">{t("common.language")}</span>
      <select
        value={i18n.language}
        onChange={(e) => setLocale(e.target.value as Locale)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
      >
        {SUPPORTED_LOCALES.map((l) => (
          <option key={l} value={l}>
            {l.toUpperCase()}
          </option>
        ))}
      </select>
    </label>
  );
}
