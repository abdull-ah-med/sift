import { apiFetch } from "@/lib/api";

export const INVITE_STORAGE_KEY = "sift_invite_token";

/** Drop spent/invalid tokens; keep tokens that still need an OIDC user session. */
export function shouldClearInviteToken(status: number, detail: string): boolean {
  if (status >= 200 && status < 300) return true;
  if (status === 401 || status >= 500) return false;
  if (status === 400 && detail.includes("requires a user session")) return false;
  return status >= 400 && status < 500;
}

function detailFromBody(body: unknown): string {
  if (!body || typeof body !== "object" || !("detail" in body)) return "";
  const detail = (body as { detail: unknown }).detail;
  return typeof detail === "string" ? detail : "";
}

/** POST a stored invite token after login; drop it on success or client error. */
export async function consumeStoredInvite(): Promise<void> {
  if (typeof window === "undefined") return;
  const token = sessionStorage.getItem(INVITE_STORAGE_KEY);
  if (!token) return;
  const r = await apiFetch("/v1/invites/accept", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
  let detail = "";
  if (r.status === 400) {
    try {
      detail = detailFromBody(await r.json());
    } catch {
      return;
    }
  }
  if (shouldClearInviteToken(r.status, detail)) {
    sessionStorage.removeItem(INVITE_STORAGE_KEY);
  }
}
