import { useTranslation } from "react-i18next";
import { createBrowserRouter, Link, type RouteObject } from "react-router-dom";
import { DashboardPage } from "@/pages/DashboardPage";
import { ForgotPasswordPage, LoginPage, RegisterPage, ResetPasswordPage } from "@/pages/AuthPages";
import { LandingPage } from "@/pages/LandingPage";
import { AppLayout, ProtectedRoute, PublicLayout } from "./layouts";

function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-md px-4 py-20 text-center">
      <h1 className="text-xl font-semibold">{t("errors.notFound")}</h1>
      <Link to="/" className="mt-4 inline-block text-brand-700 hover:underline">
        {t("errors.backHome")}
      </Link>
    </div>
  );
}

export const routes: RouteObject[] = [
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/forgot-password", element: <ForgotPasswordPage /> },
      { path: "/reset-password", element: <ResetPasswordPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [{ element: <AppLayout />, children: [{ path: "/app", element: <DashboardPage /> }] }],
  },
];

export const router = createBrowserRouter(routes);
