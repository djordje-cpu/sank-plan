/**
 * Serbian number formatting on integer para (CLAUDE.md rules 6 and design
 * system: "Numbers use Serbian formatting (1.234,56)").
 *
 * Integer arithmetic only. A non-integer `para` is a programming error and
 * throws, so a float can never reach a receipt or a report.
 */

const GROUP = ".";
const DECIMAL = ",";

function assertSafeInteger(value: number, what: string): void {
  if (!Number.isSafeInteger(value)) {
    throw new TypeError(`${what} must be a safe integer, got ${String(value)}`);
  }
}

/** 1234567 → "1.234.567" */
export function formatInt(value: number): string {
  assertSafeInteger(value, "value");
  const sign = value < 0 ? "-" : "";
  const digits = String(Math.abs(value));
  const grouped = digits.replace(/\B(?=(\d{3})+(?!\d))/g, GROUP);
  return `${sign}${grouped}`;
}

/** 123456 para → "1.234,56" */
export function formatPara(para: number): string {
  assertSafeInteger(para, "para");
  const sign = para < 0 ? "-" : "";
  const abs = Math.abs(para);
  const rsd = Math.trunc(abs / 100);
  const rest = abs % 100;
  return `${sign}${formatInt(rsd)}${DECIMAL}${String(rest).padStart(2, "0")}`;
}

/** 123456 para → "1.234,56 RSD" (non-breaking space before the unit). */
export function formatRsd(para: number): string {
  return `${formatPara(para)}\u00A0RSD`;
}

/** Percent from integer basis points: 1234 → "12,34 %"; 3000 → "30 %". */
export function formatPercentBp(basisPoints: number): string {
  assertSafeInteger(basisPoints, "basisPoints");
  const sign = basisPoints < 0 ? "-" : "";
  const abs = Math.abs(basisPoints);
  const whole = Math.trunc(abs / 100);
  const rest = abs % 100;
  const frac = rest === 0 ? "" : `${DECIMAL}${String(rest).padStart(2, "0").replace(/0$/, "")}`;
  return `${sign}${formatInt(whole)}${frac}\u00A0%`;
}
