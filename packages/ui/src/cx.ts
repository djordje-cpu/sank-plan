export type ClassValue = string | false | null | undefined;

/** Join class names, dropping falsy entries. */
export function cx(...values: ClassValue[]): string {
  return values.filter((v): v is string => typeof v === "string" && v.length > 0).join(" ");
}
