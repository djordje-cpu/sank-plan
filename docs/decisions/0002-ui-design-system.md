# 0002 — `packages/ui`: tokens, theme and components from the prototypes (P0.2)

## Context

P0.2: "`packages/ui` with tokens and components from the prototypes (button,
chip, card, table, stepper, tab). Done: Storybook with all components in light
and dark theme." CLAUDE.md fixes the stack (React 19, Tailwind with tokens from
`packages/ui` only, Vitest, sr-Latn i18n keys, ≥44 px touch targets, integer
para) and lists the palette. The two prototypes agree on the light palette but
differ in a few dark values, use sub-44 px controls, one hardcoded color, and
have no UI tab component.

## Decision

1. **Canonical source is `design/prototypes/sank-pos-demo.html`.** Its values
   match CLAUDE.md exactly (`night #171A15`); the Normativ demo differs
   (`night #1B201D`, dark `paper #15130F`, `surface #211E19`, `line #39352D`).
   Normativ screens will use the POS values; the difference is not visible at
   normal contrast and one palette is a hard requirement for a design system.

2. **Tokens live twice, provably in sync.** `src/tokens.ts` is the typed source
   (used by tests, tooling, future printing/chart code); `src/styles/tokens.css`
   mirrors it as `--sank-*` custom properties for the browser.
   `test/tokens.test.ts` parses the CSS and fails on any drift. Theme switching
   is exactly the prototype mechanism: `prefers-color-scheme: dark` unless
   `data-theme="light"`, and `data-theme="dark"` forces dark.

3. **Tailwind is CSS-first (v4) and token-only.** `src/styles/theme.css` imports
   Tailwind, wipes the default `--color-*` / `--font-*` / `--shadow-*` scales and
   re-declares only the tokens via `@theme inline`, so `bg-paper`, `text-ink`,
   `border-line-strong`, `min-h-touch` exist and `bg-red-500` does not. Apps
   import `@sank/ui/theme.css` once. `@source "../components"` lets an app's
   Tailwind see the classes used inside this package. `test/guards.test.ts`
   rejects hex/rgb/hsl literals and `bg-[…]`-style arbitrary colors in components.

4. **Derived values, not in the prototypes** (design, not regulatory, so
   derivation is allowed; recorded here so nobody mistakes them for prototype
   truth): `lineStrong` dark `#6A655B` (light `#9A9488` was hardcoded on `.btn`),
   `purple` tints (`#E8DFF3` / `#2A1F3A`; CLAUDE.md names purple but the
   prototypes never tint it), `onAccent #FFFFFF`, `onNight #F3EFE6` (text on the
   night surface must stay light in both themes; `paper` on `night` is 1.05:1
   in dark mode), and the dark `on*Tint` text colors below.

5. **Dark-mode contrast fix.** The prototypes put a hue on its own dark tint
   (ochre `#7A4F08` on `#332810` ≈ 1.9:1; green ≈ 1.6:1), unreadable and far
   below WCAG AA 4.5:1. Five tokens `onAccentTint`, `onGreenTint`, `onOchreTint`,
   `onBlueTint`, `onPurpleTint` equal the hue in light (unchanged look) and a
   lighter derived value in dark (`#F0A38B`, `#8FCBA6`, `#E0B25A`, `#8FC3DB`,
   `#C9AEEB`). `test/contrast.test.ts` computes WCAG ratios for every
   foreground/background pairing the components can render, in both themes, and
   requires ≥ 4.5:1; it also asserts that the prototype pairing fails, so the
   reason for these tokens is executable.

6. **Touch targets.** Prototype `.stepper button` is 34 px and `.btn` 42 px;
   both violate CLAUDE.md rule 8. Every interactive control in this package is
   ≥ 44 px (`--sank-size-touch`); `Button size="lg"` is 56 px for the beer path.
   A guard test requires a touch token on any component that renders a
   `<button>`; a headless Chromium run against the built Storybook measured
   44/56 px on every control in both themes.

7. **Components** (P0.2 list, prototype class in brackets): `Button` [`.btn`,
   `.btn.primary`] primary/secondary/ghost; `Chip` [`.chip.*`] six tones ×
   soft/solid; `Card` [`.card`, `.ok-card`, night hero] title/aside slots;
   `Table` [`.table`] typed generic columns, numeric = right + mono; `Stepper`
   [`.stepper`] integer, clamped, localized labels; `Tabs` — **not in the
   prototypes** (their "tab" is the bill). Built as WAI-ARIA tabs with roving
   focus in the same vocabulary, underline and segmented variants. `TabPanel`
   pairs with it.

8. **Strings** (rule 7). Components emit only accessible labels and an empty
   state; those are keys in `src/i18n.ts` with sr-Latn default and en fallback,
   a `UiLocaleProvider` and `useT()`. This is deliberately tiny — app copy stays
   in apps. A guard test rejects literal `aria-label`/`placeholder`/`title`
   attributes in components. If a shared i18n package appears, this file becomes
   an adapter; keys keep the `ui.` namespace.

9. **Money formatting** (rule 6) lives here because the design system owns
   "numbers use Serbian formatting": `formatPara` (integer para → `1.234,56`),
   `formatRsd`, `formatInt`, `formatPercentBp` (basis points). Integer-only;
   a float throws `TypeError`.

10. **Storybook 10.6 with `@storybook/react-vite`**, themes via
    `@storybook/addon-themes` `withThemeByDataAttribute` on `data-theme`, so the
    toolbar toggle exercises the same CSS path as production. One
    `vite.config.ts` (react + tailwind plugins) serves Storybook and Vitest.
    `pnpm build:storybook` is part of `pnpm check` and CI.

11. **Pins** (catalog): React 19.3.0, Vite 8.3.0, `@vitejs/plugin-react` 6.1.1,
    Tailwind 4.3.3, Storybook 10.6.0, Testing Library react 16.3.3 / dom 10.4.2
    / jest-dom 7.0.1 / user-event 14.6.7, jsdom 30.1.1. All peer ranges verified
    against each other and against Vitest 4.1's Vite range (single Vite 8 in the
    tree).

12. **TypeScript quirk recorded.** `include: [".storybook"]` is silently dropped
    by TypeScript's dot-directory rule (confirmed with `--listFilesOnly`), which
    made ESLint's project service reject those files. The tsconfig lists
    `.storybook/main.ts` and `.storybook/preview.ts` explicitly.

## Consequences

- Apps get exactly one way to color things. Anything outside the tokens is a
  lint/test failure, not a review comment.
- The dark `on*Tint` colors are ours, not the prototypes'. If the prototypes are
  updated with proper dark text colors, replace these and keep the contrast test.
- `Tabs` should be validated against the POS floor/category bar in P1.2; if the
  interaction differs, change `Tabs` here rather than styling in the app.
- Google Fonts are loaded by the app (`preview-head.html` shows the link);
  offline venues (rule 5) will need the three families self-hosted in P1.2/P1.3.

## Source

CLAUDE.md (design system, rules 6/7/8, stack); PLAN.md §6, §10 P0.2;
`design/prototypes/*.html` CSS; WCAG 2.1 §1.4.3; npm registry peer ranges as of
2026-09-22; Chromium measurement of the built Storybook.
