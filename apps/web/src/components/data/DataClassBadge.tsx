import { useTranslation } from "react-i18next";
import { cx } from "@/components/ui";

export type DataClass = "verified" | "observed" | "estimated" | "user_provided" | "mock";

const STYLES: Record<DataClass, string> = {
  verified: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  observed: "bg-sky-50 text-sky-800 ring-sky-200",
  estimated: "bg-amber-50 text-amber-800 ring-amber-200",
  user_provided: "bg-slate-100 text-slate-700 ring-slate-300",
  mock: "bg-red-600 text-white ring-red-700",
};

/** Every number in the UI carries one of these badges (docs/04-frontend-structure.md §3). */
export function DataClassBadge({ value }: { value: DataClass }) {
  const { t } = useTranslation();
  return (
    <span
      data-testid="data-class-badge"
      className={cx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset", STYLES[value])}
    >
      {t(`dataClass.${value}`)}
    </span>
  );
}
