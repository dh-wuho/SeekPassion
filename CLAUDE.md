# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instructions

This task involves multi-step reasoning. Think carefully through the problem before responding.

Provide concise, focused responses. Skip non-essential context, and keep examples minimal.

## Project status

This repository currently contains product and design documentation only — no code has been
written yet. `docs/PRD.md` is the product requirements doc; `docs/DESIGN.md` is the technical
design (architecture, tech stack, data model, and tooling). Treat both as living specs: check
them before implementing a feature, and update them when a design decision changes.

## Architecture (planned, per docs/DESIGN.md)

Monorepo layout:
- `apps/web` — Next.js (TypeScript) frontend
- `apps/api` — FastAPI (Python) backend
- `workers/monitor` — Celery tasks for company/job monitoring
- `workers/ai_pipeline` — Celery tasks for Job Matching, Resume Generation, Answer Generation
- `workers/harness` — the Job Application Harness: an LLM Browser Planning loop paired with a
  Playwright Browser Execution layer, kept behind a runtime-swappable interface
- `packages/llm` — shared LLM provider abstraction (BYOM), used by both `ai_pipeline` and `harness`
  so the LLM client isn't duplicated
- `packages/shared` — shared types/schemas between `apps/web` and `apps/api`

Python packages (`apps/api`, `workers/*`, `packages/llm`) share one **uv workspace** lockfile,
with workers depending on `packages/llm` via a local path dependency. `apps/web` is managed
separately with **pnpm** — the two toolchains don't interoperate directly; the only real coupling
point is the API contract, kept in sync via `openapi-typescript` codegen from FastAPI's OpenAPI
schema (docs/DESIGN.md §8).

Two invariants baked into the harness design that must not be relaxed without an explicit product
decision: human review is a mandatory, unconditional gate before every submission (no bypass), and
CAPTCHA/anti-bot challenges pause and hand control to the user rather than being solved
automatically (docs/DESIGN.md §5).
