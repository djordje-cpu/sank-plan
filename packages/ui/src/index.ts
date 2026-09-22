/**
 * @sank/ui — Šank design system: tokens, theme and components from the prototypes.
 *
 * Styles: import "@sank/ui/theme.css" once per app (Tailwind theme + tokens),
 * or "@sank/ui/tokens.css" for the CSS custom properties alone.
 */

export { color, font, radius, size, shadow, cssVar, COLOR_NAMES } from "./tokens.js";
export type { ColorName, Theme } from "./tokens.js";

export { formatInt, formatPara, formatRsd, formatPercentBp } from "./format.js";

export {
  t,
  useT,
  useUiLocale,
  UiLocaleContext,
  UiLocaleProvider,
  UI_LOCALES,
  UI_STRINGS,
  DEFAULT_UI_LOCALE,
} from "./i18n.js";
export type { UiLocale, UiStringKey } from "./i18n.js";

export { cx } from "./cx.js";
export type { ClassValue } from "./cx.js";

export { Button } from "./components/Button.js";
export type { ButtonProps, ButtonVariant, ButtonSize } from "./components/Button.js";

export { Chip } from "./components/Chip.js";
export type { ChipProps, ChipTone, ChipEmphasis } from "./components/Chip.js";

export { Card } from "./components/Card.js";
export type { CardProps, CardTone } from "./components/Card.js";

export { Table } from "./components/Table.js";
export type { TableProps, Column } from "./components/Table.js";

export { Stepper } from "./components/Stepper.js";
export type { StepperProps } from "./components/Stepper.js";

export { Tabs, TabPanel } from "./components/Tabs.js";
export type { TabsProps, TabItem, TabPanelProps } from "./components/Tabs.js";
