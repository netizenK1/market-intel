import { render, screen } from "@testing-library/react";
import { MemoryRouter, useRoutes } from "react-router-dom";
import { parseError } from "@/api/client";
import { routes } from "@/app/router";
import { DataClassBadge } from "@/components/data/DataClassBadge";
import { AuthProvider } from "@/features/auth/AuthProvider";

// MemoryRouter (not the data router): the data router builds fetch Requests with jsdom's AbortSignal,
// which Node's built-in fetch rejects. Route definitions are the same ones the app uses.
function AppRoutes() {
  return useRoutes(routes);
}

function renderAt(path: string) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("DataClassBadge", () => {
  it("labels mock data as DEMO", () => {
    render(<DataClassBadge value="mock" />);
    expect(screen.getByTestId("data-class-badge")).toHaveTextContent("DEMO");
  });
});

describe("routing", () => {
  it("renders the landing page", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("redirects anonymous users from /app to login", () => {
    renderAt("/app");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/kiring|log in/i);
  });

  it("warns when auth is not configured", () => {
    renderAt("/login");
    expect(screen.getByRole("alert")).toHaveTextContent("VITE_SUPABASE_URL");
  });
});

describe("parseError", () => {
  it("reads RFC 9457 problem details", async () => {
    const res = new Response(JSON.stringify({ title: "Not found", status: 404, code: "NOT_FOUND" }), { status: 404 });
    const err = await parseError(res);
    expect(err.problem.code).toBe("NOT_FOUND");
  });

  it("survives a non-JSON body", async () => {
    const err = await parseError(new Response("oops", { status: 502, statusText: "Bad Gateway" }));
    expect(err.problem.status).toBe(502);
  });
});
