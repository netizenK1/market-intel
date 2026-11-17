import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui";
import { useAuth } from "@/features/auth/AuthProvider";

const CARDS = ["newAnalysis", "calculator", "products", "reports", "savedMarkets", "recent", "compare"] as const;

export function DashboardPage() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const name = (session?.user.user_metadata as { full_name?: string } | undefined)?.full_name;

  return (
    <div>
      <h1 className="text-2xl font-semibold">
        {t("dashboard.welcome")}
        {name ? `, ${name}` : ""}
      </h1>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CARDS.map((k) => (
          <Card key={k} className="relative">
            <span className="absolute right-4 top-4 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {t("dashboard.soon")}
            </span>
            <h2 className="pr-20 font-semibold">{t(`dashboard.cards.${k}.title`)}</h2>
            <p className="mt-2 text-sm text-slate-600">{t(`dashboard.cards.${k}.text`)}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
