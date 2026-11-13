import { supabase } from "../supabaseClient";

export async function apiFetch(url, options = {}) {
  const { data, error } = await supabase.auth.getSession();
  if (error) throw new Error(error.message);

  const headers = new Headers(options.headers);
  if (data.session?.access_token) {
    headers.set("Authorization", `Bearer ${data.session.access_token}`);
  }

  let response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("Cannot reach the API. Start it with `uvicorn app.main:app --reload` from the backend folder.");
    }
    throw error;
  }

  if (!response.ok) {
    const isJson = response.headers.get("content-type")?.includes("application/json");
    const body = isJson ? await response.json() : {};
    const detail = body.detail;
    if (!detail && response.status >= 500) {
      throw new Error("The API server is unavailable. Start it with `uvicorn app.main:app --reload` from the backend folder.");
    }
    const message = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => {
          const location = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(" → ") : "";
          return [location, item.msg || JSON.stringify(item)].filter(Boolean).join(": ");
        }).join("; ")
        : detail && typeof detail === "object"
          ? detail.message || detail.error?.message || JSON.stringify(detail)
          : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return response;
}
