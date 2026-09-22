import { describe, expect, it } from "vitest";

import { PACKAGE_NAME } from "../src/index.js";

describe("@sank/gost", () => {
  it("exports its package name", () => {
    expect(PACKAGE_NAME).toBe("@sank/gost");
  });
});
