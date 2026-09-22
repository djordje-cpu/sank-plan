# 0001 — Monorepo toolchain and workspace scaffold (P0.1)

## Context

P0.1 asks for "monorepo, TypeScript strict, lint, format, CI" with the done-when
`pnpm -r build` passes. PLAN.md §6 fixes the workspace list (7 apps, 7 packages)
but pins no tool versions, and several tools shipped new majors in 2026 whose
peer ranges do not yet agree. CLAUDE.md also refers to a PLAN.md "status table"
that did not exist, and to a repo layout the uploaded files did not follow.

## Decision

1. **Layout.** Files are moved to the layout in CLAUDE.md: `docs/PLAN.md`,
   `docs/business_model_engine.py`, `docs/certification/*`, `docs/decisions/*`,
   `design/prototypes/*`. The uploaded `sank-repo.zip` (a byte-identical
   duplicate of those files) is removed and `*.zip` is git-ignored.

2. **All 14 workspaces are scaffolded now** as minimal placeholders
   (`src/index.ts` exporting `PACKAGE_NAME`, one smoke test, `typecheck` /
   `test` / `build` scripts). This makes `pnpm -r build` mean 14 real `tsc`
   runs rather than a trivially empty pass, fixes the workspace graph early, and
   lets each later work package replace its own stub in place. No domain, UI or
   fiscal logic is introduced here.

3. **Naming.** Packages are `@sank/<name>`. pnpm's `--filter` matches an
   unscoped name against the scoped one, so the commands in CLAUDE.md
   (`pnpm --filter api dev`) work unchanged. Verified: `pnpm --filter api typecheck`
   runs `@sank/api`.

4. **Toolchain pins** live in a single pnpm `catalog:` in `pnpm-workspace.yaml`
   so every workspace resolves the same version:

   | Tool                   | Version | Why this line                                                     |
   | ---------------------- | ------- | ----------------------------------------------------------------- |
   | Node                   | 22      | `.nvmrc`, `engines`, CI                                           |
   | pnpm                   | 10.33.0 | `packageManager` field; CI reads it                               |
   | TypeScript             | 5.9.3   | typescript-eslint peer is `<6.1.0`; TS 7 (native port) not usable |
   | ESLint                 | 10.11.0 | 9.x is marked deprecated/EOL on the registry                      |
   | typescript-eslint      | 8.70.1  | supports ESLint `^10`, TS `<6.1`                                  |
   | @eslint/js             | 10.0.1  | pairs with ESLint 10                                              |
   | eslint-config-prettier | 10.1.8  | peer `eslint >=7`                                                 |
   | Prettier               | 3.9.8   |                                                                   |
   | Vitest                 | 4.1.11  | peer `@types/node ^22` satisfied                                  |
   | @types/node            | 22.20.4 | matches Node 22                                                   |

5. **TypeScript strictness** goes beyond `strict: true` in `tsconfig.base.json`:
   `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`,
   `noImplicitReturns`, `noFallthroughCasesInSwitch`,
   `noPropertyAccessFromIndexSignature`, `useUnknownInCatchVariables`,
   `isolatedModules`, `verbatimModuleSyntax`. Module system is ESM with
   `NodeNext`. Vite/Astro apps will override `moduleResolution: bundler` and
   `lib: DOM` in their own `tsconfig.json` when they are built (P0.5, P1.2 …);
   the base stays Node-first because `hub`, `api` and every package are Node.

6. **Lint** is the flat config at the root: `@eslint/js` recommended,
   typescript-eslint `recommendedTypeChecked` via `projectService`, plus
   `no-explicit-any: error` (CLAUDE.md definition of done), inline type imports,
   `_`-prefixed unused vars allowed. `eslint-config-prettier` is last.
   `design/prototypes/` and `docs/` are not linted.

7. **Format** is Prettier with `printWidth 100`, double quotes, trailing commas.
   `docs/PLAN.md` and `docs/certification/` are excluded: they are authored
   documents and the regulatory contract; tooling must not rewrite them.

8. **CI** is one GitHub Actions job on push to `main` and on pull requests:
   `pnpm install --frozen-lockfile`, then lint, format check, typecheck, test,
   build — in that order so the cheapest failure surfaces first. Concurrency
   cancels superseded runs on the same ref.

9. **Status table** is added to PLAN.md §10 (`### Status radnih paketa`) because
   CLAUDE.md requires updating one at the end of every package and none existed.

## Consequences

- `pnpm check` is the local equivalent of CI; run it before every push.
- Upgrading TypeScript to 7 waits for typescript-eslint to widen its peer range;
  track it in a later ADR.
- Every package stub must be replaced, not extended, by its own work package.
  The placeholder `PACKAGE_NAME` export and smoke test are deleted then.
- `packages/fiscal-core` carries its rule-1 header from day one; its version stays
  `0.0.0` until P1.4 ports `fiscal_reference.py`.

## Source

CLAUDE.md (rules, stack, layout, commands, definition of done); PLAN.md §6, §10;
npm registry metadata and peer ranges as of 2026-09-22.
