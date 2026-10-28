export const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
export async function api(path, options = {}) {
  const res = await fetch(`${API}/api${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : `Request failed (${res.status}). Check inputs or backend status.`,
    );
  }
  return res.status === 204 ? null : res.json();
}
export const fmt = (n) => Number(n ?? 0).toLocaleString("en-US");
