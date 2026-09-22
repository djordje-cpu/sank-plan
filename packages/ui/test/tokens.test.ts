import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { COLOR_NAMES, color, cssVar, shadow } from "../src/tokens.js";

const here = dirname(fileURLToPath(import.meta.url));
const tokensCss = readFileSync(join(here, "../src/styles/tokens.css"), "utf8");
const themeCss = readFileSync(join(here, "../src/styles/theme.css"), "utf8");

/** Extract `--name: value;` pairs from the block that starts at `selector {`. */
function block(css: string, selector: string): Map<string, string> {
  const start = css.indexOf(selector);
  if (start === -1) throw new Error(`selector not found: ${selector}`);
  const open = css.indexOf("{", start);
  let depth = 0;
  let end = open;
  for (let i = open; i < css.length; i++) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}") {
      depth--;
      if (depth === 0) {
        end = i;
        break;
      }
    }
  }
  const body = css.slice(open + 1, end);
  const out = new Map<string, string>();
  for (const m of body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    out.set(m[1] ?? "", (m[2] ?? "").replace(/\s+/g, " ").trim());
  }
  return out;
}

const norm = (hex: string) => hex.toLowerCase();

describe("tokens.css mirrors tokens.ts", () => {
  const light = block(tokensCss, ":root {");
  const dark = block(tokensCss, ':root[data-theme="dark"]');
  const darkMedia = block(tokensCss, ':root:not([data-theme="light"])');

  it.each(COLOR_NAMES)("light %s", (name) => {
    expect(light.get(cssVar(name))).toBe(norm(color.light[name]));
  });

  it.each(COLOR_NAMES)("dark %s", (name) => {
    expect(dark.get(cssVar(name))).toBe(norm(color.dark[name]));
  });

  it("the prefers-color-scheme block is identical to the data-theme=dark block", () => {
    expect([...darkMedia.entries()].sort()).toEqual([...dark.entries()].sort());
  });

  it("shadow tokens match", () => {
    const squash = (s: string) => s.replace(/\s+/g, "").replace(/0\./g, ".");
    expect(squash(light.get("--sank-shadow") ?? "")).toBe(squash(shadow.light));
    expect(squash(dark.get("--sank-shadow") ?? "")).toBe(squash(shadow.dark));
  });

  it("declares no light-only or dark-only color", () => {
    const lightColors = [...light.keys()].filter((k) => !/shadow|font|radius|size/.test(k));
    const darkColors = [...dark.keys()].filter((k) => !/shadow/.test(k));
    expect(darkColors.sort()).toEqual(lightColors.sort());
  });
});

describe("theme.css exposes every token to Tailwind", () => {
  it.each(COLOR_NAMES)("--color-* for %s", (name) => {
    const tailwindName = cssVar(name).replace("--sank-", "--color-");
    expect(themeCss).toContain(`${tailwindName}: var(${cssVar(name)})`);
  });

  it("wipes the default palette so only tokens exist", () => {
    expect(themeCss).toMatch(/--color-\*:\s*initial/);
    expect(themeCss).toMatch(/--font-\*:\s*initial/);
  });
});

describe("cssVar", () => {
  it("kebab-cases camelCase and digits", () => {
    expect(cssVar("surface2")).toBe("--sank-surface-2");
    expect(cssVar("accentTint")).toBe("--sank-accent-tint");
    expect(cssVar("lineStrong")).toBe("--sank-line-strong");
    expect(cssVar("ink")).toBe("--sank-ink");
  });
});

describe("palette sanity", () => {
  it("dark and light differ on every surface but share the brand hues", () => {
    for (const n of ["paper", "surface", "surface2", "line", "ink", "ink2"] as const) {
      expect(color.light[n]).not.toBe(color.dark[n]);
    }
    for (const n of ["accent", "green", "ochre", "blue", "purple", "onAccent"] as const) {
      expect(color.light[n]).toBe(color.dark[n]);
    }
  });
});
