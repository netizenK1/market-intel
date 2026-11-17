import { useState, type FormEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Alert, Button, Card, Field } from "@/components/ui";
import { useAuth } from "@/features/auth/AuthProvider";
import { supabase } from "@/lib/supabase";

const MIN_PASSWORD = 10;

function AuthShell({ title, children, footer }: { title: string; children: ReactNode; footer?: ReactNode }) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-12">
      <Card className="p-6 sm:p-8">
        <h1 className="text-xl font-semibold">{title}</h1>
        {!supabase && (
          <div className="mt-4">
            <Alert kind="error">{t("auth.notConfigured")}</Alert>
          </div>
        )}
        <div className="mt-6">{children}</div>
      </Card>
      {footer && <p className="mt-4 text-center text-sm text-slate-600">{footer}</p>}
    </div>
  );
}

function useSubmit() {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function run(fn: () => Promise<{ error: { message: string } | null }>): Promise<boolean> {
    setBusy(true);
    setError(null);
    try {
      const { error: err } = await fn();
      if (err) {
        setError(err.message);
        return false;
      }
      return true;
    } catch {
      setError(t("errors.generic"));
      return false;
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, run };
}

export function LoginPage() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { busy, error, run } = useSubmit();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const from = (location.state as { from?: string } | null)?.from ?? "/app";

  if (session) return <Navigate to={from} replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!supabase) return;
    const client = supabase;
    if (await run(() => client.auth.signInWithPassword({ email, password }))) navigate(from, { replace: true });
  }

  return (
    <AuthShell
      title={t("auth.loginTitle")}
      footer={
        <>
          {t("auth.noAccount")}{" "}
          <Link className="font-medium text-brand-700 hover:underline" to="/register">
            {t("nav.register")}
          </Link>
        </>
      }
    >
      <form className="space-y-4" onSubmit={(e) => void onSubmit(e)}>
        {error && <Alert kind="error">{error}</Alert>}
        <Field id="email" type="email" autoComplete="email" required label={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
        <Field id="password" type="password" autoComplete="current-password" required label={t("auth.password")} value={password} onChange={(e) => setPassword(e.target.value)} />
        <div className="flex items-center justify-between">
          <Link to="/forgot-password" className="text-sm text-brand-700 hover:underline">
            {t("auth.forgotLink")}
          </Link>
          <Button type="submit" disabled={busy || !supabase}>
            {t("auth.submitLogin")}
          </Button>
        </div>
      </form>
    </AuthShell>
  );
}

export function RegisterPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const { busy, error, run } = useSubmit();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);

  if (session) return <Navigate to="/app" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!supabase) return;
    const client = supabase;
    const ok = await run(() =>
      client.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName, locale: i18n.language },
          emailRedirectTo: `${window.location.origin}/app`,
        },
      }),
    );
    if (ok) setDone(true);
  }

  return (
    <AuthShell
      title={t("auth.registerTitle")}
      footer={
        <>
          {t("auth.haveAccount")}{" "}
          <Link className="font-medium text-brand-700 hover:underline" to="/login">
            {t("nav.login")}
          </Link>
        </>
      }
    >
      {done ? (
        <Alert kind="success">{t("auth.checkEmail")}</Alert>
      ) : (
        <form className="space-y-4" onSubmit={(e) => void onSubmit(e)}>
          {error && <Alert kind="error">{error}</Alert>}
          <Field id="fullName" autoComplete="name" required maxLength={200} label={t("auth.fullName")} value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Field id="email" type="email" autoComplete="email" required label={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
          <Field
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={MIN_PASSWORD}
            label={t("auth.password")}
            hint={t("auth.passwordHint")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" className="w-full" disabled={busy || !supabase}>
            {t("auth.submitRegister")}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}

export function ForgotPasswordPage() {
  const { t } = useTranslation();
  const { busy, error, run } = useSubmit();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!supabase) return;
    const client = supabase;
    const ok = await run(() =>
      client.auth.resetPasswordForEmail(email, { redirectTo: `${window.location.origin}/reset-password` }),
    );
    // Same message whether or not the email exists (no account enumeration).
    if (ok) setSent(true);
  }

  return (
    <AuthShell title={t("auth.forgotTitle")}>
      {sent ? (
        <Alert kind="success">{t("auth.resetSent")}</Alert>
      ) : (
        <form className="space-y-4" onSubmit={(e) => void onSubmit(e)}>
          {error && <Alert kind="error">{error}</Alert>}
          <Field id="email" type="email" autoComplete="email" required label={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
          <Button type="submit" className="w-full" disabled={busy || !supabase}>
            {t("auth.submitForgot")}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}

export function ResetPasswordPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { busy, error, run } = useSubmit();
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!supabase) return;
    const client = supabase;
    // The recovery link signs the user in temporarily; updateUser sets the new password.
    if (await run(() => client.auth.updateUser({ password }))) {
      setDone(true);
      setTimeout(() => navigate("/app", { replace: true }), 1200);
    }
  }

  return (
    <AuthShell title={t("auth.resetTitle")}>
      {done ? (
        <Alert kind="success">{t("auth.passwordUpdated")}</Alert>
      ) : (
        <form className="space-y-4" onSubmit={(e) => void onSubmit(e)}>
          {error && <Alert kind="error">{error}</Alert>}
          <Field
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={MIN_PASSWORD}
            label={t("auth.password")}
            hint={t("auth.passwordHint")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" className="w-full" disabled={busy || !supabase}>
            {t("auth.submitReset")}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
