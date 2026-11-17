import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { en } from "./locales/en";
import { uz } from "./locales/uz";

export const SUPPORTED_LOCALES = ["uz", "en"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

const STORAGE_KEY = "locale";

function initialLocale(): Locale {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "uz" || saved === "en") return saved;
  } catch {
    /* storage unavailable */
  }
  return "uz";
}

void i18n.use(initReactI18next).init({
  resources: { uz: { translation: uz }, en: { translation: en } },
  lng: initialLocale(),
  fallbackLng: "uz",
  interpolation: { escapeValue: false },
  returnObjects: true,
});

export function setLocale(locale: Locale): void {
  void i18n.changeLanguage(locale);
  document.documentElement.lang = locale;
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    /* ignore */
  }
}

export default i18n;
