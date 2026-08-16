/** Drop spent/invalid tokens; keep tokens that still need an OIDC user session. */
export function shouldClearInviteToken(status: number, detail: string): boolean {
  if (status >= 200 && status < 300) return true;
  if (status === 401 || status >= 500) return false;
  if (status === 400 && detail.includes("requires a user session")) return false;
  return status >= 400 && status < 500;
}
