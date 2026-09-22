/**
 * Design tokens — the typed source of truth for the Šank design system.
 *
 * Values come from design/prototypes/sank-pos-demo.html (canonical: it matches
 * CLAUDE.md "Design system"). `styles/tokens.css` mirrors these as CSS custom
 * properties; `test/tokens.test.ts` proves the two never drift.
 *
 * Derived (not in the prototypes, see ADR 0002): `lineStrong` dark value,
 * `purple` tints, `onAccent`, and the dark `on*Tint` text colors (the prototype
 * reuses the hue itself on its dark tint, which fails WCAG contrast).
 */

export const color = {
  light: {
    paper: "#F3EFE6",
    surface: "#FFFFFF",
    surface2: "#FAF8F3",
    line: "#E3DDD0",
    lineStrong: "#9A9488",
    ink: "#1B201D",
    ink2: "#555C57",
    night: "#171A15",
    night2: "#242920",
    onNight: "#F3EFE6",
    accent: "#A33A1F",
    accentTint: "#F6E3DB",
    onAccentTint: "#A33A1F",
    onAccent: "#FFFFFF",
    green: "#2C6446",
    greenTint: "#E1EEE5",
    onGreenTint: "#2C6446",
    ochre: "#7A4F08",
    ochreTint: "#F6EBD3",
    onOchreTint: "#7A4F08",
    blue: "#1F5F7A",
    blueTint: "#DDEBF1",
    onBlueTint: "#1F5F7A",
    purple: "#6B3FA0",
    purpleTint: "#E8DFF3",
    onPurpleTint: "#6B3FA0",
  },
  dark: {
    paper: "#131210",
    surface: "#1F1C17",
    surface2: "#191611",
    line: "#37332B",
    lineStrong: "#6A655B",
    ink: "#F3EFE6",
    ink2: "#B7B2A6",
    night: "#0C0B09",
    night2: "#1A1712",
    onNight: "#F3EFE6",
    accent: "#A33A1F",
    accentTint: "#3A241D",
    onAccentTint: "#F0A38B",
    onAccent: "#FFFFFF",
    green: "#2C6446",
    greenTint: "#1C2F22",
    onGreenTint: "#8FCBA6",
    ochre: "#7A4F08",
    ochreTint: "#332810",
    onOchreTint: "#E0B25A",
    blue: "#1F5F7A",
    blueTint: "#17262B",
    onBlueTint: "#8FC3DB",
    purple: "#6B3FA0",
    purpleTint: "#2A1F3A",
    onPurpleTint: "#C9AEEB",
  },
} as const;

export type ColorName = keyof typeof color.light;
export type Theme = keyof typeof color;

export const font = {
  display: "'Fraunces', Georgia, serif",
  sans: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
  mono: "'IBM Plex Mono', 'SFMono-Regular', Menlo, monospace",
} as const;

/** Pixel radii from the prototypes: controls 8, cards/chips 12, pills. */
export const radius = { sm: 8, md: 12, pill: 999 } as const;

/**
 * CLAUDE.md rule 8: touch targets ≥ 44 px. The prototypes use 34 px (stepper)
 * and 42 px (button); the design system lifts every interactive control to 44.
 */
export const size = { touch: 44, chip: 24 } as const;

export const shadow = {
  light: "0 1px 2px rgba(27,32,29,.06), 0 8px 24px rgba(27,32,29,.08)",
  dark: "0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.35)",
} as const;

/** `surface2` → `--sank-surface-2`, `accentTint` → `--sank-accent-tint`. */
export function cssVar(name: ColorName): `--sank-${string}` {
  const kebab = name.replace(/([a-z])([A-Z0-9])/g, "$1-$2").toLowerCase();
  return `--sank-${kebab}`;
}

export const COLOR_NAMES = Object.keys(color.light) as ReadonlyArray<ColorName>;
