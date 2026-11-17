import i18n from "@/i18n";
import { supabase } from "@/lib/supabase";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

/** RFC 9457 problem details returned by the backend. */
export interface Problem {
  type?: string;
  title: string;
  status: number;
  code: string;
  detail?: string;
  fields?: Record<string, string>;
  request_id?: string;
}

export class ApiError extends Error {
  constructor(public readonly problem: Problem) {
    super(problem.detail ?? problem.title);
    this.name = "ApiError";
  }
}

export async function parseError(res: Response): Promise<ApiError> {
  try {
    const body = (await res.json()) as Partial<Problem>;
    return new ApiError({
      title: body.title ?? res.statusText,
      status: body.status ?? res.status,
      code: body.code ?? "HTTP_ERROR",
      detail: body.detail,
      fields: body.fields,
      request_id: body.request_id,
    });
  } catch {
    return new ApiError({ title: res.statusText || "Error", status: res.status, code: "HTTP_ERROR" });
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Accept-Language", i18n.language);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
