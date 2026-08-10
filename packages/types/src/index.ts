/** Canonical workspace identity used by smoke tests. */
export const packageName = "@sift/types" as const;

export function getPackageName(): typeof packageName {
  return packageName;
}
