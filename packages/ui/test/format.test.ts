import { describe, expect, it } from "vitest";

import { formatInt, formatPara, formatPercentBp, formatRsd } from "../src/format.js";

describe("formatInt", () => {
  it.each([
    [0, "0"],
    [7, "7"],
    [999, "999"],
    [1000, "1.000"],
    [1234567, "1.234.567"],
    [-1234, "-1.234"],
  ])("%d → %s", (n, s) => {
    expect(formatInt(n)).toBe(s);
  });

  it("rejects non-integers and unsafe integers", () => {
    expect(() => formatInt(1.5)).toThrow(TypeError);
    expect(() => formatInt(Number.NaN)).toThrow(TypeError);
    expect(() => formatInt(2 ** 53)).toThrow(TypeError);
  });
});

describe("formatPara (integer para → Serbian RSD)", () => {
  it.each([
    [0, "0,00"],
    [5, "0,05"],
    [100, "1,00"],
    [123456, "1.234,56"],
    [184000, "1.840,00"],
    [100000000, "1.000.000,00"],
    [-32050, "-320,50"],
  ])("%d para → %s", (para, s) => {
    expect(formatPara(para)).toBe(s);
  });

  it("never accepts a float (rule 6)", () => {
    expect(() => formatPara(12.34)).toThrow(TypeError);
  });

  it("formatRsd appends a non-breaking unit", () => {
    expect(formatRsd(123456)).toBe("1.234,56\u00A0RSD");
  });
});

describe("formatPercentBp", () => {
  it.each([
    [0, "0\u00A0%"],
    [3000, "30\u00A0%"],
    [1234, "12,34\u00A0%"],
    [2850, "28,5\u00A0%"],
    [-400, "-4\u00A0%"],
    [123456, "1.234,56\u00A0%"],
  ])("%d bp → %s", (bp, s) => {
    expect(formatPercentBp(bp)).toBe(s);
  });
});
