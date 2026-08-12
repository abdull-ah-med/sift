/** Map failed API responses to a three-part UI error without storing bodies. */
export function humanApiError(
  status: number,
  fallback: string,
): { title: string; detail: string; action: string } {
  if (status === 401 || status === 403) {
    return {
      title: "Not authorized",
      detail: "This request was rejected for the current credentials.",
      action: "Sign in again or check the API key scopes.",
    };
  }
  if (status === 404) {
    return {
      title: "Not found",
      detail: "The collection or document is missing, or the id is wrong.",
      action: "Return to collections and open the item again.",
    };
  }
  if (status >= 500) {
    return {
      title: "Server error",
      detail: "sift could not complete this request.",
      action: "Retry in a moment.",
    };
  }
  return {
    title: fallback,
    detail: "The API rejected this request.",
    action: "Fix the fields and retry.",
  };
}

export function formatApiError(status: number, fallback: string): string {
  const e = humanApiError(status, fallback);
  return `${e.title}. ${e.detail} ${e.action}`;
}
