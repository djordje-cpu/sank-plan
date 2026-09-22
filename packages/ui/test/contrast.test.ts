/**
 * WCAG 2.x contrast for every text/background pairing the components emit,
 * in both themes. Chips are 12 px semibold, so the small-text threshold (4.5:1)
 * applies everywhere; nothing here is allowed to fall back to the 3:1 large-text
 * exemption.
 */
import { describe, expect, it } from "vitest";

import { color, type ColorName, type Theme } from "../src/tokens.js";

const AA_SMALL = 4.5;

function channel(hex2: string): number {
  const c = parseInt(hex2, 16) / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** Relative luminance per WCAG (sRGB). */
export function luminance(hex: string): number {
  const h = hex.replace("#", "");
  return (
    0.2126 * channel(h.slice(0, 2)) +
    0.7152 * channel(h.slice(2, 4)) +
    0.0722 * channel(h.slice(4, 6))
  );
}

export function contrast(fg: string, bg: string): number {
  const [a, b] = [luminance(fg), luminance(bg)];
  const [hi, lo] = a > b ? [a, b] : [b, a];
  return (hi + 0.05) / (lo + 0.05);
}

interface Pair {
  where: string;
  fg: ColorName;
  bg: ColorName;
}

// Every foreground/background combination a component can render.
const PAIRS: ReadonlyArray<Pair> = [
  // page + surfaces
  { where: "body text on paper", fg: "ink", bg: "paper" },
  { where: "body text on surface", fg: "ink", bg: "surface" },
  { where: "muted text on surface", fg: "ink2", bg: "surface" },
  { where: "muted text on surface-2", fg: "ink2", bg: "surface2" },
  { where: "muted text on paper", fg: "ink2", bg: "paper" },
  // Button
  { where: "Button primary", fg: "onAccent", bg: "accent" },
  { where: "Button secondary", fg: "ink", bg: "surface" },
  { where: "Button ghost hover", fg: "ink", bg: "surface2" },
  // Chip soft
  { where: "Chip soft neutral", fg: "ink2", bg: "surface2" },
  { where: "Chip soft accent", fg: "onAccentTint", bg: "accentTint" },
  { where: "Chip soft green", fg: "onGreenTint", bg: "greenTint" },
  { where: "Chip soft ochre", fg: "onOchreTint", bg: "ochreTint" },
  { where: "Chip soft blue", fg: "onBlueTint", bg: "blueTint" },
  { where: "Chip soft purple", fg: "onPurpleTint", bg: "purpleTint" },
  // Chip solid
  { where: "Chip solid neutral", fg: "paper", bg: "ink" },
  { where: "Chip solid accent", fg: "onAccent", bg: "accent" },
  { where: "Chip solid green", fg: "onAccent", bg: "green" },
  { where: "Chip solid ochre", fg: "onAccent", bg: "ochre" },
  { where: "Chip solid blue", fg: "onAccent", bg: "blue" },
  { where: "Chip solid purple", fg: "onAccent", bg: "purple" },
  // Card tones
  { where: "Card ok", fg: "ink", bg: "greenTint" },
  { where: "Card night", fg: "onNight", bg: "night" },
  // Table
  { where: "Table header", fg: "ink2", bg: "surface" },
  { where: "Table accent row", fg: "ink", bg: "accentTint" },
  { where: "Table ok row", fg: "ink", bg: "greenTint" },
  // Tabs
  { where: "Tab selected", fg: "ink", bg: "surface" },
  { where: "Tab idle", fg: "ink2", bg: "paper" },
  { where: "Tab segmented idle", fg: "ink2", bg: "surface2" },
  // Stepper
  { where: "Stepper button", fg: "ink", bg: "surface2" },
];

const THEMES: ReadonlyArray<Theme> = ["light", "dark"];

describe.each(THEMES)("%s theme meets WCAG AA (≥ 4.5:1) for small text", (theme) => {
  it.each(PAIRS)("$where", ({ fg, bg }) => {
    const ratio = contrast(color[theme][fg], color[theme][bg]);
    expect(ratio, `${fg} on ${bg} = ${ratio.toFixed(2)}:1`).toBeGreaterThanOrEqual(AA_SMALL);
  });
});

describe("the math", () => {
  it("black on white is 21:1 and identical colors are 1:1", () => {
    expect(contrast("#000000", "#FFFFFF")).toBeCloseTo(21, 5);
    expect(contrast("#A33A1F", "#A33A1F")).toBeCloseTo(1, 5);
  });
});

describe("why on*Tint exists (documents the prototype defect, ADR 0002)", () => {
  it("the prototype's hue-on-its-own-dark-tint pairing fails AA", () => {
    // What the prototype does in dark mode: ochre text on ochre tint.
    expect(contrast(color.dark.ochre, color.dark.ochreTint)).toBeLessThan(AA_SMALL);
    expect(contrast(color.dark.green, color.dark.greenTint)).toBeLessThan(AA_SMALL);
    // In light mode the same pairing is fine, so the light on*Tint equals the hue.
    for (const hue of ["accent", "green", "ochre", "blue", "purple"] as const) {
      const on = `on${hue[0]?.toUpperCase() ?? ""}${hue.slice(1)}Tint` as ColorName;
      expect(color.light[on]).toBe(color.light[hue]);
    }
  });
});
