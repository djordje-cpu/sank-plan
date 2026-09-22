/**
 * Static guards for the design-system rules in CLAUDE.md. They read the
 * component sources so a violation fails CI before a reviewer sees it.
 */
import { readdirSync, readFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const componentsDir = join(here, "../src/components");
const storiesDir = join(here, "../stories");

const componentFiles = readdirSync(componentsDir).filter((f) => f.endsWith(".tsx"));
const components = componentFiles.map((f) => basename(f, ".tsx"));
const read = (f: string) => readFileSync(join(componentsDir, f), "utf8");

// P0.2 scope: dugme, čip, kartica, tabela, stepper, tab.
const REQUIRED = ["Button", "Chip", "Card", "Table", "Stepper", "Tabs"] as const;

describe("P0.2 scope", () => {
  it.each(REQUIRED)("%s component exists", (name) => {
    expect(components).toContain(name);
  });
});

describe("no arbitrary colors (CLAUDE.md: Tailwind with tokens from packages/ui only)", () => {
  const ARBITRARY = [
    /#[0-9a-fA-F]{3,8}\b/, // hex literals
    /\brgba?\(/, // rgb()/rgba()
    /\bhsla?\(/, // hsl()/hsla()
    /\b(?:bg|text|border|outline|ring|fill|stroke|from|to|via|shadow)-\[/, // bg-[…] etc.
  ];

  it.each(componentFiles)("%s", (file) => {
    const src = read(file);
    for (const re of ARBITRARY) {
      expect(src, `${file} matches ${re}`).not.toMatch(re);
    }
  });
});

describe("touch targets ≥ 44 px (CLAUDE.md rule 8)", () => {
  const interactive = componentFiles.filter((f) => /<button\b/.test(read(f)));

  it("covers every component that renders a <button>", () => {
    expect(interactive.length).toBeGreaterThan(0);
  });

  it.each(interactive)("%s sizes its buttons with a touch token", (file) => {
    expect(read(file)).toMatch(/\b(?:min-h-touch|size-touch|h-touch)\b/);
  });
});

describe("no hardcoded user-facing strings (CLAUDE.md rule 7)", () => {
  // Any aria-label / placeholder / title literal must come from t(...).
  it.each(componentFiles)("%s", (file) => {
    const src = read(file);
    const literal = /(?:aria-label|placeholder|title)=["'][^"']+["']/g;
    expect(src.match(literal) ?? []).toEqual([]);
  });
});

describe("Storybook coverage (P0.2 done-when: every component has stories)", () => {
  const storyFiles = readdirSync(storiesDir).filter((f) => f.endsWith(".stories.tsx"));
  const storied = storyFiles.map((f) => basename(f, ".stories.tsx"));

  it.each(components)("%s has a stories file", (name) => {
    expect(storied).toContain(name);
  });

  it.each(storyFiles)("%s exports a default meta and at least one story", (file) => {
    const src = readFileSync(join(storiesDir, file), "utf8");
    expect(src).toMatch(/export default meta/);
    expect(src).toMatch(/export const \w+: Story/);
  });
});

describe("theme switching", () => {
  it("preview toggles light and dark via data-theme, matching tokens.css", () => {
    const preview = readFileSync(join(here, "../.storybook/preview.ts"), "utf8");
    expect(preview).toMatch(/withThemeByDataAttribute/);
    expect(preview).toMatch(/attributeName:\s*"data-theme"/);
    expect(preview).toMatch(/dark:\s*"dark"/);
    expect(preview).toMatch(/light:\s*"light"/);
  });
});
