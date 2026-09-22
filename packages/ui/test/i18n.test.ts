import { describe, expect, it } from "vitest";

import { DEFAULT_UI_LOCALE, UI_LOCALES, UI_STRINGS, t, type UiStringKey } from "../src/i18n.js";

const KEYS = Object.keys(UI_STRINGS.en) as ReadonlyArray<UiStringKey>;

describe("ui strings", () => {
  it("default locale is sr-Latn (rule 7)", () => {
    expect(DEFAULT_UI_LOCALE).toBe("sr-Latn");
  });

  it.each(UI_LOCALES)("%s defines every key with non-empty text", (locale) => {
    for (const key of KEYS) {
      expect(UI_STRINGS[locale][key].trim().length).toBeGreaterThan(0);
    }
  });

  it("every key is namespaced under ui.", () => {
    for (const key of KEYS) expect(key.startsWith("ui.")).toBe(true);
  });

  it("t() resolves sr-Latn by default and en on request", () => {
    expect(t("ui.table.empty")).toBe("Nema podataka");
    expect(t("ui.table.empty", "en")).toBe("No data");
  });

  it("sr-Latn and en differ for every key (no untranslated copies)", () => {
    for (const key of KEYS) {
      expect(UI_STRINGS["sr-Latn"][key]).not.toBe(UI_STRINGS.en[key]);
    }
  });
});
