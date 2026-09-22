/**
 * UI strings for the design-system components (CLAUDE.md rule 7: sr-Latn by
 * default, en fallback, i18n keys, never hardcoded).
 *
 * Scope is deliberately tiny: only strings the components themselves emit
 * (accessible labels, empty states). App copy lives with the apps. If a shared
 * i18n package appears later, this module becomes a thin adapter (ADR 0002).
 */
import { createContext, useContext } from "react";

export const UI_LOCALES = ["sr-Latn", "en"] as const;
export type UiLocale = (typeof UI_LOCALES)[number];
export const DEFAULT_UI_LOCALE: UiLocale = "sr-Latn";

const en = {
  "ui.stepper.increment": "Add one",
  "ui.stepper.decrement": "Remove one",
  "ui.table.empty": "No data",
  "ui.tabs.label": "Sections",
} as const;

export type UiStringKey = keyof typeof en;

const srLatn: Record<UiStringKey, string> = {
  "ui.stepper.increment": "Dodaj jedan",
  "ui.stepper.decrement": "Oduzmi jedan",
  "ui.table.empty": "Nema podataka",
  "ui.tabs.label": "Sekcije",
};

export const UI_STRINGS: Record<UiLocale, Record<UiStringKey, string>> = {
  "sr-Latn": srLatn,
  en,
};

/** Resolve a key in `locale`, falling back to en, then to the key itself. */
export function t(key: UiStringKey, locale: UiLocale = DEFAULT_UI_LOCALE): string {
  return UI_STRINGS[locale][key] ?? UI_STRINGS.en[key] ?? key;
}

export const UiLocaleContext = createContext<UiLocale>(DEFAULT_UI_LOCALE);
export const UiLocaleProvider = UiLocaleContext.Provider;

export function useUiLocale(): UiLocale {
  return useContext(UiLocaleContext);
}

export function useT(): (key: UiStringKey) => string {
  const locale = useUiLocale();
  return (key) => t(key, locale);
}
