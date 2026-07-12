# Seek Passion — Design

This document describes the technical design for Seek Passion, based on the
requirements in [PRD.md](./PRD.md). It covers architecture, tech stack, data
model, and the design of the Job Application Harness.

---

## 1. Architecture Overview

```text
                    ┌─────────────────┐
                    │   Web Frontend   │  Next.js (TS)
                    └────────┬─────────┘
                             │ REST/JSON (JWT auth)
                    ┌────────▼─────────┐
                    │    API Service    │  FastAPI (Python)
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                     │
┌───────▼───────┐   ┌────────▼────────┐   ┌────────▼────────┐
│  Data Layer    │   │   Task Queue    │   │  Object Storage  │
│  SQLite/Postgres│   │  Celery + Redis │   │  S3 / MinIO      │
└────────────────┘   └────────┬────────┘   └─────────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
        ┌────────▼──────┐ ┌───▼────────┐ ┌──▼─────────────────┐
        │ Company Monitor │ │ AI Pipeline│ │ Job Application     │
        │ Workers         │ │ (Matching, │ │ Harness              │
        │                 │ │ Resume,    │ │ (Planning + Playwright│
        │                 │ │ Answers)   │ │  Execution)           │
        └─────────────────┘ └─────┬──────┘ └───────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  LLM Provider     │  BYOM: OpenAI, Anthropic,
                          │  Abstraction      │  Gemini, GLM, Ollama, ...
                          └───────────────────┘
```

The API Service handles synchronous requests (CRUD, auth, reads). Anything
long-running or scheduled (crawling, resume generation, browser sessions)
runs as a Celery task so the API stays responsive and retries/failures are
handled uniformly.

---

## 2. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Next.js (React, TypeScript) | Dashboard-heavy UI (§5 of PRD); SSR for data-heavy tables |
| Backend API | Python, FastAPI | Async-native; best ecosystem fit for LLM orchestration and Playwright |
| Browser automation | Playwright (Python) | Deterministic execution layer, driven by an LLM planning layer (§2.6, §8) |
| Database | SQLite → PostgreSQL via SQLAlchemy + Alembic | Matches PRD's explicit migration path (§9 Scalability) |
| Task queue | Celery + Redis | Retry semantics for crawling, browser sessions, notifications (§8 "Retry handling") |
| Auth | Auth.js (NextAuth) + JWT validated by FastAPI | Email + Google login (§6) with minimal custom code |
| Object storage | S3-compatible (MinIO for self-hosting) | Holds generated artifacts (resume PDFs, session screenshots) that don't belong as DB rows — Postgres/SQLite store only the pointer (`file_url`). Not a backup store. |
| LLM abstraction | Thin custom provider interface (no heavy agent framework) | Matches "Modular Intelligence" (§2.5) and BYOM (§2.7) |

---

## 3. System Components

### 3.1 Web Frontend
Renders the 10 product pages from PRD §5 (Dashboard, Companies, Jobs,
Experience Library, Resume Library, Applications, Browser Sessions, AI
Settings, Profile, Settings). Talks to the API Service only — no direct
DB or LLM access.

### 3.2 API Service
Stateless FastAPI service. Owns:
- Auth (issues/validates JWTs, delegates OAuth to Auth.js)
- CRUD for all entities in §4
- Enqueuing Celery tasks (crawl now, generate resume, start application)
- Read APIs for browser session status, logs, screenshots

### 3.3 Company Monitor Workers
A single Celery Beat schedule scans the **platform-curated company catalog
every 4 hours (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)** — a 4-hour
cadence spreads coverage across business hours in every timezone so postings
are picked up within ~4h wherever they originate, while staying far kinder to
ATS APIs than aggressive polling. Each
company is a shared, global entity scanned **once per run regardless of how
many users subscribe to it**; the scan normalizes postings, deduplicates
against existing jobs, then enqueues a per-user Job Matching task for each
subscriber (§4 `Subscription`). Users cannot poll arbitrary companies — the
catalog is admin-managed — but any subscriber can trigger a manual refresh of
a catalog company on demand between scheduled runs (PRD §5.2).

Distinguishes two ingestion strategies:
- **ATS API adapters** (preferred, stable) — **MVP ships Greenhouse and
  Lever first**: both expose public job-board read APIs (no scraping needed
  for discovery) and have comparatively light bot-protection on their
  application forms, which keeps the harness within the CAPTCHA-handoff
  design (§5). Together they cover a large share of the startup/scale-up
  companies the primary persona targets (PRD §3.1). Workday, iCIMS, and
  other heavy-ATS platforms are deferred to V2 (PRD §10) — they carry the
  highest scraping/bot-protection difficulty for the lowest MVP payoff.
- **HTML scraping** — fallback for custom career pages, fragile by nature;
  flagged separately in monitoring so breakage is visible rather than silent

### 3.4 AI Pipeline
Each capability from PRD §2.5 is an independent Celery task with a narrow
input/output contract:
- **Job Matching** — Job + Profile + Experience Library → Match Score, Missing Skills
- **Resume Generation** — Job + retrieved Experience snippets → Resume draft
- **Answer Generation** — Job + question + retrieved Experience snippets → Answer draft
- **Browser Planning** — page state → next action (used by the Harness)

All generation tasks follow the retrieval-first pattern from PRD §2.3:
retrieve from the Experience Library before calling the LLM, and pass only
verified snippets as grounding context — never ask the LLM to invent content.

**Retrieval strategy (MVP): pass the whole Experience Library into context,
no embeddings or vector store.** The primary persona (PRD §3.1) realistically
has a few dozen snippets — roughly 3k–9k tokens — which fits current context
windows with room to spare, so full-library grounding is both simpler and
more accurate than top-K similarity (no retriever recall miss). It also keeps
BYOM clean: no dependency on any provider's embedding model. `retrieve()` is
a defined function boundary — at MVP it returns everything; a V2 vector-search
implementation returns top-K behind the same interface, with no other change.
Revisit when a user's library outgrows the context budget or when the per-call
token cost/latency threatens the PRD §9 "resume generation under 20s" target.

**Truthfulness enforcement.** "Never hallucinate" (PRD §2.2) is enforced, not
just declared: after generation, a validation step checks that factual claims
in the output (companies, titles, metrics, technologies) trace back to the
source snippets passed in. Content that fails validation is flagged to the
user rather than silently surfaced. This is the concrete mechanism behind the
principle — without it, "never hallucinate" is only aspirational.

### 3.5 Job Application Harness
See §5 below — this is the most novel and highest-risk component.

### 3.6 LLM Provider Abstraction
A single interface (`generate(prompt, context) -> response`,
`estimate_cost(...)`) implemented per provider (OpenAI, Anthropic, Gemini,
GLM, Ollama). API keys are encrypted at rest (§9 PRD Security) and never
logged. Swapping providers must not touch any AI Pipeline task code.

Lives as a shared package (`packages/llm/`), not inside `workers/ai_pipeline/`
— Browser Planning (§5) also calls the LLM to decide page actions, so both
workers depend on the same client rather than each owning a copy.

---

## 4. Data Model

Types are written Postgres-first (`JSONB`, `UUID`) since SQLite is the
day-one target per §9 of the PRD; SQLAlchemy maps `JSONB`→`JSON` and
`UUID`→`TEXT` transparently on SQLite, so the schema doesn't change across
the migration.

### User
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| email | TEXT UNIQUE | |
| auth_provider | ENUM(email, google) | |
| created_at | TIMESTAMP | |

### Profile
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User, UNIQUE) | 1:1 |
| full_name | TEXT | |
| phone | TEXT | |
| work_authorization | TEXT | |
| sponsorship_required | BOOLEAN | |
| desired_locations | JSONB | array of strings |
| salary_expectation | TEXT | |
| linkedin_url / github_url / portfolio_url | TEXT | |

### Company
Global, platform-curated catalog entity — **not per-user**. Users relate to
companies only through `Subscription`.
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| name | TEXT | |
| career_url | TEXT | |
| ats_type | TEXT NULLABLE | greenhouse / lever / workday / custom |
| monitoring_status | ENUM(active, paused) | admin toggle; paused companies are skipped by the scheduled scan |
| last_crawl_at | TIMESTAMP NULLABLE | |

### Subscription
Join table — a user's set of subscriptions is their "my companies" list.
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User) | |
| company_id | UUID (FK → Company) | |
| created_at | TIMESTAMP | |

UNIQUE(user_id, company_id)

### Job
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| company_id | UUID (FK → Company) | |
| title | TEXT | |
| location | TEXT | |
| employment_type | TEXT | |
| level | TEXT | |
| description | TEXT | |
| posted_at | TIMESTAMP | |
| apply_url | TEXT | |
| dedupe_hash | TEXT UNIQUE | hash(company_id + title + apply_url); prevents duplicate rows from re-crawls |
| status | ENUM(open, expired) | |
| created_at | TIMESTAMP | |

### JobMatch
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| job_id | UUID (FK → Job) | |
| user_id | UUID (FK → User) | |
| match_score | FLOAT | normalized 0.0–1.0; formatted as a percentage in the UI (PRD §5.3) |
| missing_skills | JSONB | array of strings |
| matching_experience_ids | JSONB | array of ExperienceSnippet ids |
| recommendation | TEXT | |
| computed_at | TIMESTAMP | |

UNIQUE(job_id, user_id)

### ExperienceSnippet
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User) | |
| title | TEXT | |
| company | TEXT | |
| description | TEXT | |
| technologies / achievements / metrics / tags | JSONB | arrays |
| content_hash | TEXT | normalized hash of title+company+description; powers the duplicate-detection feature (PRD §5.4) — a near-match on insert warns the user rather than hard-blocking |
| created_at / updated_at | TIMESTAMP | |

### Resume
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User) | |
| job_id | UUID (FK → Job, NULLABLE) | null = general-purpose resume, not job-targeted |
| version | INTEGER | |
| included_snippet_ids | JSONB | array of ExperienceSnippet ids |
| file_url | TEXT | pointer into object storage (§3, not stored in DB) |
| generated_at | TIMESTAMP | |

### Application
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User) | |
| job_id | UUID (FK → Job) | |
| resume_id | UUID (FK → Resume) | |
| status | ENUM(Draft, Preparing, Waiting Review, Applying, Submitted, Failed, Rejected, Accepted) | |
| generated_answers | JSONB | question → answer map |
| submitted_at | TIMESTAMP NULLABLE | |
| created_at / updated_at | TIMESTAMP | |

### BrowserSession
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| application_id | UUID (FK → Application, UNIQUE) | 1:1 |
| status | ENUM(running, paused_review, paused_captcha, failed, completed) | |
| current_page_url | TEXT | |
| action_history | JSONB | array of {action, timestamp, result} |
| screenshot_urls | JSONB | array of pointers into object storage |
| logs_url | TEXT | pointer into object storage |
| last_error | TEXT NULLABLE | |
| updated_at | TIMESTAMP | |

### AIProviderConfig
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User) | |
| provider | TEXT | openai / anthropic / gemini / glm / ollama |
| model | TEXT | |
| encrypted_api_key | BYTEA | encrypted at rest, never logged (§6) |
| prompt_preferences | JSONB | |
| is_active | BOOLEAN | |

### Notification
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User) | |
| type | TEXT | new_job / review_required / application_result / session_paused |
| channel | ENUM(in_app, email) | MVP delivers in-app (always) + email (opt-out per PRD §5.10). Dispatched by a Celery task; push/SMS deferred to V2 |
| payload | JSONB | |
| read_at | TIMESTAMP NULLABLE | |
| created_at | TIMESTAMP | |

Relationships: `User 1—1 Profile`, `User 1—N ExperienceSnippet`,
`User N—M Company` (via `Subscription`), `Company 1—N Job` (global),
`Job 1—N JobMatch/Resume/Application`, `Application 1—1 BrowserSession`.

---

## 5. Job Application Harness Design

The harness is split into **Planning** and **Execution**, per PRD §2.5/§2.6,
so the business logic never depends on a specific browser runtime.

```text
┌─────────────────────┐
│  Browser Planning     │  LLM reads page state (DOM/accessibility tree,
│  (LLM decision loop)  │  screenshot) → emits one structured action
└──────────┬────────────┘  e.g. {action: "fill", selector: "#email", value: "..."}
           │
┌──────────▼────────────┐
│  Browser Execution     │  Playwright executes the action deterministically,
│  (Playwright runtime)  │  captures screenshot, verifies expected result
└──────────┬────────────┘
           │
      loop until: application complete, error, or checkpoint reached
```

### State machine
`Launch → Navigate → Fill → Verify → (repeat) → PendingReview → Submit → Complete`,
with `Failed` and `PausedForUser` as side-states reachable from any step.

The harness step, the persisted `BrowserSession.status`, and the user-facing
`Application.status` are three layers describing the same lifecycle at
different granularities. They map as follows — use these names consistently;
they are not interchangeable synonyms:

| Harness step | BrowserSession.status | Application.status |
|---|---|---|
| Launch / Navigate / Fill / Verify | `running` | `Applying` |
| PendingReview | `paused_review` | `Waiting Review` |
| (CAPTCHA hit) | `paused_captcha` | `Applying` |
| (missing user input) | `paused_review` | `Waiting Review` |
| Submit → Complete | `completed` | `Submitted` |
| Failed | `failed` | `Failed` |

### Hard requirements (from PRD decisions)
- **Human review is a mandatory, unconditional gate.** Every application
  transitions through `PendingReview` before `Submit`; there is no code
  path that submits without it (PRD §2.1).
- **CAPTCHA / anti-bot challenges pause and hand control to the user.**
  Automated solving/evasion is explicitly out of scope — Playwright does
  not evade bot detection by default and attempting to would increase ToS
  risk, not reduce it (PRD §8).
- **Retry handling** applies only to recoverable failures (timeouts,
  transient navigation errors), not to review or CAPTCHA pauses.

### Runtime abstraction
`Browser Execution` is defined behind an interface
(`launch()`, `execute(action)`, `screenshot()`, `close()`) so Playwright can
be swapped for another runtime (e.g. a future AI browser runtime) without
touching Planning or any upstream business logic (PRD §2.6).

### Action schema
Browser Planning emits one structured action per step via the LLM
provider's native structured-output/tool-calling feature — never free-form
text — so Execution and the state machine can pattern-match reliably:

```json
{
  "action": "click | fill | select | upload | wait | request_review | pause_captcha | ask_user | submit | done",
  "selector": "string | null",   // prefer accessibility-tree role/label over raw CSS — more stable across ATS redesigns
  "value": "string | null",
  "file_ref": "string | null",   // pointer into object storage, for upload actions
  "reasoning": "string"          // short rationale; stored in BrowserSession.action_history for audit
}
```

`request_review`, `pause_captcha`, `ask_user`, and `done` are first-class
terminal actions — the state machine transitions in response to the action
type, not by parsing natural language. An unrecognized page should always
resolve to `ask_user` rather than the LLM improvising an action outside
this closed set.

---

## 6. Security

- API keys and OAuth tokens encrypted at rest; never appear in logs
- Browser sessions run isolated (one browser context per application)
- Audit log for every submitted application: who approved, when, what was submitted
- PII (resumes, profile data) scoped per-user; no cross-user data access at the query layer

---

## 7. Repo Structure (proposed)

```text
seek_passion/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/           # FastAPI backend
├── workers/
│   ├── monitor/       # Company monitoring tasks
│   ├── ai_pipeline/    # Matching, Resume, Answer generation tasks (uses packages/llm)
│   └── harness/        # Job Application Harness — Planning (uses packages/llm) + Playwright Execution
├── packages/
│   ├── llm/             # Shared LLM provider abstraction (BYOM), used by ai_pipeline and harness
│   └── shared/          # TypeScript API types GENERATED from FastAPI's OpenAPI schema (see §8); consumed by web, never hand-edited
└── docs/
    ├── PRD.md
    └── DESIGN.md
```

---

## 8. Tooling & Project Management

Single git repo (monorepo). The Python and Node ecosystems are managed
independently by their own toolchains — they don't share a package manager
or lockfile, only the git history and a thin orchestration layer.

### Python (`apps/api`, `workers/*`, `packages/llm`)
Managed as a **uv workspace**: one shared lockfile at the repo root, with
`workers/ai_pipeline` and `workers/harness` depending on `packages/llm` as
a local path dependency rather than a duplicated copy. `uv run` / `uv sync`
per package during development.

### Node (`apps/web`)
Managed with **pnpm**. `packages/shared` holds only the TypeScript types
generated from the API's OpenAPI schema (below), so it isn't a hand-authored
package; a pnpm workspace is introduced only if genuinely shared, hand-written
TS code appears later.

### Keeping the API contract in sync
The one real coupling point between the two toolchains: FastAPI's Pydantic
models are the source of truth for the API shape, and `apps/web` never
hand-writes types against them. A build step runs `openapi-typescript`
against FastAPI's generated OpenAPI schema to produce TypeScript types
consumed by the frontend — so a backend field rename breaks the frontend
build instead of failing silently at runtime.

### Local development
**docker-compose** brings up the full stack (API, Celery worker, Celery
Beat, Redis, Postgres, web) with hot-reload volumes for both apps. A root
**Makefile** wraps common commands (`make dev`, `make test`, `make lint`)
so contributors don't need to remember which toolchain a given package uses.

### CI
GitHub Actions with **path-filtered jobs**: changes under `apps/api/`,
`workers/`, or `packages/llm/` trigger the Python job (ruff, mypy, pytest);
changes under `apps/web/` trigger the Node job (eslint, tsc, build). A
change to only one side doesn't run the other side's pipeline.

### Testing strategy
Per CLAUDE.md this is a test-driven codebase: every feature ships with
integration tests, and the two hardest-to-test components need a deterministic
approach so tests stay fast, free, and CI-safe:

- **Harness / Playwright** — integration tests run the planning+execution loop
  against **recorded static ATS form fixtures** (saved Greenhouse/Lever HTML),
  not the live sites. This asserts the harness fills and navigates correctly
  without hitting a real ATS, avoiding flakiness and ToS issues. The mandatory
  review gate and CAPTCHA-pause paths (§5) each get an explicit test proving no
  code path submits without review.
- **LLM calls** — the `packages/llm` interface is mocked (or replays recorded
  responses) in tests, so AI Pipeline and Browser Planning tests are
  deterministic and incur no token cost. A small, separately-gated suite may
  exercise real providers, kept out of the default CI run.
- **Truthfulness** — the grounding/validation step (§3.4) is unit-tested with
  fixtures that deliberately inject unsupported claims, asserting they are
  flagged rather than passed through.

---

## 9. Open Questions

- Monetization model is intentionally out of scope for this document.
  BYOM (§2.7 PRD, §3.6, `AIProviderConfig` in §4) is implemented regardless
  of pricing — the technical requirement doesn't depend on how/whether the
  product charges for it.
