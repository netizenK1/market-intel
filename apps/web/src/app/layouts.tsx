import { useTranslation } from "react-i18next";
import { Link, Navigate, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Button } from "@/components/ui";
import { useAuth } from "@/features/auth/AuthProvider";
import { supabase } from "@/lib/supabase";

function Logo() {
  const { t } = useTranslation();
  return (
    <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">MI</span>
      <span className="hidden sm:inline">{t("brand")}</span>
    </Link>
  );
}

export function PublicLayout() {
  const { t } = useTranslation();
  const { session } = useAuth();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Logo />
          <nav className="flex items-center gap-2">
            <LanguageSwitcher />
            {session ? (
              <Link to="/app" className="text-sm font-medium text-brand-700 hover:underline">
                {t("nav.dashboard")}
              </Link>
            ) : (
              <>
                <Link to="/login" className="px-2 text-sm font-medium text-slate-700 hover:text-slate-900">
                  {t("nav.login")}
                </Link>
                <Link
                  to="/register"
                  className="rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  {t("nav.register")}
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-6 text-xs text-slate-500">
          © {new Date().getFullYear()} {t("brand")}. {t("landing.footer")}
        </div>
      </footer>
    </div>
  );
}

export function ProtectedRoute() {
  const { session, loading } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();
  if (loading) return <div className="p-8 text-sm text-slate-500">{t("common.loading")}</div>;
  if (!session) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

export function AppLayout() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const navigate = useNavigate();

  async function logout() {
    await supabase?.auth.signOut();
    navigate("/", { replace: true });
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Logo />
          <div className="flex items-center gap-3">
            <NavLink to="/app" end className="hidden text-sm font-medium text-slate-700 sm:inline">
              {t("nav.dashboard")}
            </NavLink>
            <LanguageSwitcher />
            <span className="hidden max-w-[12rem] truncate text-sm text-slate-500 md:inline">{session?.user.email}</span>
            <Button variant="secondary" onClick={() => void logout()}>
              {t("nav.logout")}
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
