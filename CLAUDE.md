# CLAUDE.md — Šank

Šank is a front-of-house-first restaurant platform for Serbia: POS with live table tabs, kitchen display, guest QR menu and pay-at-table, and Normativ margin analytics on top of SEF e-invoices and ESIR sales. Read `docs/PLAN.md` before touching anything. The plan is the spec; this file is how we work.

## Non-negotiable rules

1. `packages/fiscal-core` is certified software. Never change it as a side effect of another task. Any change there needs an ADR in `docs/decisions/`, a version bump, a changelog entry, and a note that re-approval by Poreska uprava is required. UI, catalog, KDS and analytics must never import fiscal internals; they call the small public API only.
2. No fiscalization without a live PFR response. There is no "fiscalize later" queue, no fake receipts, no receipt printed without the PFR-signed payload. If the L-PFR is unreachable, checkout fails loudly.
3. Every order mutation is a command with a client-generated UUID and produces an event in `order_event`. Table state is a projection. Never mutate table state directly.
4. Every query is tenant-scoped. `tenant_id` on every table, Postgres RLS on, tests that prove cross-tenant reads fail.
5. Offline first for the venue: `apps/pos` and `apps/kds` must work against `apps/hub` on LAN with the internet down. Sync is outbox/inbox, idempotent, ordered per venue.
6. Money is integer para (1 RSD = 100 para) end to end. Menu prices are VAT-inclusive; margins and food-cost ratios are computed on net. Never use floats for money.
7. Language: user-facing strings are sr-Latn by default with an en fallback, via i18n keys, never hardcoded. Code, comments, commits and docs are in English.
8. Touch targets ≥ 44 px, one tap to add an item, running total always visible while ordering. If a change adds a tap to the beer path, it needs a reason in the PR.

## Stack

pnpm workspaces, TypeScript strict everywhere. React 19 + Vite PWAs (`pos`, `kds`, `gost`, `admin`), Astro for `web`, Fastify for `api`, Node single-binary for `hub`. Drizzle ORM: PostgreSQL 16 in cloud, SQLite (better-sqlite3) on hub. zod at every boundary. Zustand for client state, Dexie for client cache. WebSocket for realtime. Vitest for unit/integration, Playwright for e2e. Tailwind with tokens from `packages/ui` only (no arbitrary colors).

## Repo layout

```
apps/{pos,kds,gost,admin,web,hub,api}
packages/{fiscal-core,domain,ui,sync,sef-client,printing,db}
docs/{PLAN.md,business_model_engine.py,decisions/,certification/{FISCAL-SPEC.md,fiscal_reference.py,certification_matrix.csv,esir_questionnaire_answers.csv,submission_checklist.txt,*.pdf}}
design/prototypes/   original HTML prototypes (Šank POS demo, Normativ screens) — reference only
```

## Design system (from prototypes)

Fonts: Fraunces (display), IBM Plex Sans (UI), IBM Plex Mono (numbers). Tokens: paper `#F3EFE6`, surface `#FFFFFF`, line `#E3DDD0`, ink `#1B201D`, ink2 `#555C57`, night `#171A15`, accent `#A33A1F` (paprika; alternates blue `#1F5F7A`, purple `#6B3FA0`), green `#2C6446`, ochre `#7A4F08`. Dark theme via `[data-theme="dark"]` and `prefers-color-scheme`. Numbers use Serbian formatting (1.234,56). Warm, editorial, no gratuitous gradients.

## Commands

```
pnpm install
pnpm -r typecheck && pnpm -r test && pnpm -r build
pnpm --filter api dev        # http://localhost:4000
pnpm --filter hub dev        # http://localhost:4100 (LAN service)
pnpm --filter pos dev        # http://localhost:5173
pnpm --filter web dev        # http://localhost:4321
pnpm db:migrate && pnpm db:seed   # seeds "Restoran Primer"
```

## Working style

Work package by package from `docs/PLAN.md` §10, in order. Before coding a package, write its "done when" as failing tests, then make them pass. Keep PRs small and named `P1.2: pos ordering flow`. Update `docs/PLAN.md` status table at the end of each package. When something in the plan is wrong or ambiguous, write a short ADR proposing the change instead of silently deviating.

Never invent regulatory details. `docs/certification/FISCAL-SPEC.md` is the contract for `packages/fiscal-core`; it cites the four official PURS documents that sit next to it (Tehnički vodič; Tehničko uputstvo v1.17; ESIR and L-PFR manual-testing instructions). `docs/certification/fiscal_reference.py` is the executable reference: port it 1:1 (schema, money, rules, receipt agents) and keep its 22 self-tests green in `packages/fiscal-core/test/reference.test.ts`. `certification_matrix.csv` lists 36 test cases that must each have an automated test before P2.1. Values marked VERIFY in the spec are confirmed on the sandbox first, then recorded in an ADR. For SEF UBL fields use the SEF API docs; if a document is missing, stop and ask for it.

## Definition of done (every package)

Typecheck clean, tests green, no `any`, i18n keys added for new strings, dark and light themes checked, offline path checked for pos/kds/hub work, ADR written for any architectural choice, PLAN status updated.
