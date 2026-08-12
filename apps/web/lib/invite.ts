import { apiFetch } from "@/lib/api";

export const INVITE_STORAGE_KEY = "sift_invite_token";

/** POST a stored invite token after login; drop it on success or client error. */
export async function consumeStoredInvite(): Promise<void> {
  if (typeof window === "undefined") return;
  const token = sessionStorage.getItem(INVITE_STORAGE_KEY);
  if (!token) return;
  const r = await apiFetch("/v1/invites/accept", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
  if (r.ok || (r.status >= 400 && r.status < 500 && r.status !== 401)) {
    sessionStorage.removeItem(INVITE_STORAGE_KEY);
  }
}
