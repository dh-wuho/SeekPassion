# SeekPassion Agent — Design Document

## 1. System Overview

A single-user autonomous agent that runs as a local background daemon. It discovers jobs, evaluates and ranks them against the user's resume, tailors resume snippets per job, and drives batched application submission through a browser — pausing at two explicit user review gates before anything is submitted.

```
┌─────────────────────────────────────────────────────────┐
│                      Daemon Process                     │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐   ┌─────────────┐   │
│  │  Discovery  │──> │ Evaluation  │──>│  Tailoring  │   │
│  │    Loop     │    │   Pipeline  │   │   Pipeline  │   │
│  └─────────────┘    └─────────────┘   └──────┬──────┘   │
│                                             │           │
│  ┌──────────────────────────────────────────▼───────┐   │
│  │              FastAPI Web UI (Review Gate 1)      │   │
│  └──────────────────────────────────────┬───────────┘   │
│                                         │               │
│  ┌──────────────────────────────────────▼───────────┐   │
│  │         Submission Module (Playwright)           │   │
│  │    batch fill → email notify → user confirm      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              SQLite (SQLAlchemy)                │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
seekpassion/
├── config.yaml                  # user configuration
├── resume/
│   ├── static.yaml              # Tier 1: contact, education, certifications
│   └── pool.yaml                # Tier 2: experience and project entries
├── seekpassion/
│   ├── main.py                  # daemon entry point
│   ├── config.py                # config loader and validation
│   ├── db/
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── session.py           # engine and session factory
│   ├── discovery/
│   │   ├── base.py              # Scraper protocol / base class
│   │   ├── company_board.py     # ATS-specific scrapers
│   │   ├── linkedin.py          # Playwright-based LinkedIn scraper
│   │   └── deduplicator.py      # cross-source deduplication
│   ├── evaluation/
│   │   ├── jd_parser.py         # LLM: JD → structured fields
│   │   ├── profile.py           # loads Tier 1 + Tier 2 into candidate profile
│   │   ├── matcher.py           # algorithmic fit scoring
│   │   ├── success.py           # algorithmic success probability
│   │   └── ranker.py            # weighted combination + filtering
│   ├── tailoring/
│   │   ├── selector.py          # top-N snippet retrieval from pool
│   │   ├── polisher.py          # LLM: rewrite for JD alignment + ATS friendliness
│   │   └── suggestions.py       # propose Tier 2 updates to user
│   ├── llm/
│   │   ├── base.py              # LLMProvider protocol
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   └── mistral.py
│   ├── submission/
│   │   ├── batch_manager.py     # orchestrates batches, email gates
│   │   ├── form_filler.py       # Playwright form automation
│   │   └── ats/
│   │       ├── base.py          # ATS handler protocol
│   │       ├── greenhouse.py
│   │       ├── lever.py
│   │       ├── workday.py
│   │       ├── icims.py
│   │       ├── taleo.py
│   │       ├── smartrecruiters.py
│   │       └── ashby.py
│   ├── web/
│   │   ├── app.py               # FastAPI application
│   │   ├── routes/
│   │   │   ├── review.py        # Phase 1 review endpoints
│   │   │   └── status.py        # application tracking endpoints
│   │   └── templates/           # Jinja2 HTML templates
│   └── notifications/
│       └── email.py             # SMTP email sender
└── tests/
    ├── fixtures/                # sample JDs, resume files, ATS page snapshots
    ├── test_evaluation.py
    ├── test_tailoring.py
    └── test_submission.py
```

---

## 3. Data Models

### 3.1 Resume Files (user-maintained)

**`resume/static.yaml` — Tier 1**
```yaml
name: Jane Doe
email: jane@example.com
phone: +1-555-000-0000
address: San Francisco, CA
education:
  - degree: B.S. Computer Science
    school: UC Berkeley
    year: 2018
certifications:
  - AWS Solutions Architect (2022)
```

**`resume/pool.yaml` — Tier 2**
```yaml
experiences:
  - id: exp-001
    title: Senior Software Engineer
    company: Acme Corp
    start: 2021-03
    end: 2024-01
    tags: [python, distributed-systems, latency, infra]
    bullets:
      - Reduced P99 latency by 40% by redesigning cache invalidation strategy
      - Led migration of monolith to microservices serving 50M req/day

projects:
  - id: proj-001
    title: Real-time Analytics Pipeline
    tags: [kafka, python, ml, latency, streaming]
    bullets:
      - Built end-to-end streaming pipeline processing 1M events/sec with sub-100ms lag
```

### 3.2 Database Schema (SQLite via SQLAlchemy)

#### `jobs`
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| source | enum | `linkedin`, `company_board` |
| company | text | |
| title | text | |
| description | text | raw JD text |
| location | text | |
| remote | bool | |
| date_posted | date | nullable |
| job_url | text | job listing page; apply button is here |
| ats_platform | enum | greenhouse, lever, workday, … |
| discovered_at | datetime | |
| jd_parsed | JSON | `{required_skills, preferred_skills, years_exp, education_req, responsibilities}` |
| fit_score | float | 0–100, null until evaluated |
| success_probability | float | 0–100, null until evaluated |
| ranking_score | float | weighted combination |
| submitted_at | datetime | nullable |
| notes | text | manual updates |
| status | enum | `new → evaluated → tailored → phase1_approved → submitted → interviewing → offer → rejected` |

#### `tailored_applications`
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| job_id | FK → jobs | |
| created_at | datetime | |
| selected_snippets | JSON | `[{snippet_id, polished_text, edited_text}]`; `edited_text` null if user accepted LLM version |
| skills_reordered | JSON | ordered skill list for this job |
| status | enum | `draft → phase1_approved → phase2_reviewing → submitted` |


#### `llm_suggestions`
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| snippet_id | text | references pool.yaml entry id |
| job_id | FK → jobs | job that triggered the suggestion |
| original_text | text | bullet text at time of suggestion |
| suggested_text | text | proposed replacement bullet |
| reason | text | LLM explanation |
| status | enum | `pending → approved → rejected` |
| created_at | datetime | |

---

## 4. Module Design

### 4.1 LLM Abstraction (`llm/base.py`)

All LLM calls go through a single protocol. Switching providers is a config change only.

```python
class LLMProvider(Protocol):
    async def complete(self, system: str, user: str, **kwargs) -> str: ...
    async def embed(self, text: str) -> list[float]: ...

def get_provider(config: LLMConfig) -> LLMProvider:
    match config.provider:
        case "anthropic": return AnthropicProvider(config)
        case "openai":    return OpenAIProvider(config)
        case "gemini":    return GeminiProvider(config)
        case "mistral":   return MistralProvider(config)
```

LLM is used for:
- JD parsing (structured extraction)
- Snippet selection ranking (when embedding similarity alone isn't sufficient)
- Snippet polishing (JD alignment + ATS friendliness)
- Tier 2 improvement suggestions

LLM is **not** used for:
- Fit score calculation (algorithmic after parsing)
- Success probability calculation (algorithmic)
- Static/Tier 1 data

### 4.2 Discovery Loop

Runs continuously as an async task. Two sub-scrapers run independently:

- **CompanyBoardScraper** — polls each configured careers URL, detects new postings by comparing against known job IDs in the DB. ATS platform detected from URL pattern or page markup.
- **LinkedInScraper** — Playwright browser session with randomized delays (`request_delay_min`–`request_delay_max`). On CAPTCHA detection: logs event, pauses LinkedIn scraper, resumes company board scraper. LinkedIn scraper retries after a configurable backoff period.

Both feed into **Deduplicator**: jobs are matched by `(company, title, job_url)` hash. Cross-source duplicates keep the record with the richer data.

The scraper always scans all configured sources and applies two filters at scrape time before writing to DB:

1. **Age filter** — jobs older than `discovery.max_job_age_weeks` are dropped.
2. **Title filter** — each title is classified by domain and seniority:
   - Domain classification matches against keyword sets per domain (`engineering` → engineer, developer, architect, scientist, researcher, sre, devops, ml; `sales` → account executive, sales; etc.). Only jobs matching a domain in `discovery.domains` are kept.
   - Junior keywords (intern, junior, associate, entry-level) → dropped immediately.
   - Senior keywords (senior, staff, principal, lead, architect) → kept.
   - Generic titles (no seniority signal) → kept provisionally, flagged as `generic_title=true`.
   - Custom `discovery.title_exclude` keywords drop any title containing them.

3. **Years filter (evaluation time)** — jobs flagged `generic_title=true` are dropped after JD parsing if `jd_parsed.years_exp < discovery.min_years_required`. Jobs with no `years_exp` in the JD pass through.

Evaluation runs on all `new` jobs that passed the title filter. The top-ranked results are then passed to tailoring and submission, capped at `daily_application_limit` per 24-hour window.

### 4.3 Evaluation Pipeline

Triggered for each new job record. Runs sequentially per job:

1. **JDParser** — LLM call to extract structured fields from raw description: `required_skills`, `preferred_skills`, `years_exp`, `education_req`, `responsibilities`. Result stored in `jobs.jd_parsed`.

2. **Matcher** — algorithmic fit score (0–100):
   - Skill overlap: Jaccard similarity between candidate tags and `required_skills + preferred_skills` (required weighted 2×)
   - Experience match: delta between candidate total YOE and `years_exp`; score decays for gaps >2 years
   - Title match: token overlap between past titles and job title
   - Education match: binary pass/fail on degree level requirement
   - Composite: weighted average of dimensions

3. **SuccessEstimator** — algorithmic success probability (0–100):
   - Seniority gap penalty: over/under-qualified reduces score
   - Posting age penalty: linear decay after 14 days posted
   - Location/remote compatibility: binary factor
   - No LLM involved — deterministic from structured fields

4. **Ranker** — `ranking_score = fit_weight × fit_score + success_weight × success_probability`. Writes scores back to `jobs` table.

### 4.4 Tailoring Pipeline

Triggered for each evaluated job where `fit_score >= min_fit_score`.

**Step 1 — Select**
Retrieve top-N entries from `pool.yaml` by relevance to the job:
- Compute embedding for JD `responsibilities + required_skills` (one LLM embed call, cached per job)
- Compute embeddings for each pool entry (cached, recomputed only when pool.yaml changes)
- Rank by cosine similarity, take top `snippet_select_n`

**Step 2 — Polish**
Single LLM call per selected snippet with system prompt instructing:
- Mirror exact keyword forms from the JD
- Lead with strong action verb + quantifiable outcome
- Ensure skill terms appear in context
- No fabrication — reframe only

Result stored as `tailored_applications.selected_snippets` with `original_text` and `polished_text` side-by-side.

**Step 3 — Suggest (async, non-blocking)**
If polished text scores significantly better than original on a heuristic check (keyword density, action verb presence), queue an `llm_suggestions` record for user review in the web UI.

### 4.5 Review Web UI (Phase 1)

FastAPI app running on `localhost:8000`. Single-page per job batch showing:
- Ranked list of prepared applications
- Per-job: fit score, success probability, key strengths, key gaps
- Side-by-side original vs polished snippets for each selected entry
- Inline edit fields for any polished snippet
- Pending Tier 2 suggestions with approve/reject buttons
- "Confirm batch" button → sets jobs to `phase1_approved`, triggers Phase 2

### 4.6 Submission Module (Phase 2)

**BatchManager** orchestrates the submission loop:

```
while approved_jobs remaining:
    batch = next submission_batch_size jobs
    open batch_size Playwright tabs concurrently
    for each tab: FormFiller.fill(job, tailored_application)
    stop at ATS review/confirm step (do not click final submit)
    send email notification with batch summary + confirm link
    wait for user confirmation (polls DB for confirmation flag)
    submit all tabs in batch
    record applications in DB
```

**FormFiller** detects ATS platform from `jobs.ats_platform` and delegates to the appropriate handler. Each ATS handler implements:
- `navigate(url)` — load the application page
- `fill_fields(profile, tailored_application)` — fill all standard fields
- `upload_resume(path)` — upload resume file if required (generated from tailored data on the fly as plain text)
- `reach_review_step()` → returns when stopped at the ATS's own review page

**Email notifications** use SMTP (configurable). Each batch notification contains the list of companies/roles in the batch and a localhost confirmation URL.

---

## 5. Concurrency Model

The daemon runs as a single Python process using `asyncio`. Major components run as async tasks:

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(discovery_loop())
        tg.create_task(evaluation_loop())
        tg.create_task(tailoring_loop())
        tg.create_task(web_ui())          # FastAPI via uvicorn
```

Each loop polls the DB for work items and sleeps when idle. Playwright operations run in a dedicated thread pool (`asyncio.to_thread`) to avoid blocking the event loop.

---

## 6. ATS Platform Detection

Detected from `job_url` pattern before scraping and confirmed from page content:

| Pattern | Platform |
|---|---|
| `greenhouse.io` | Greenhouse |
| `lever.co` | Lever |
| `myworkdayjobs.com` | Workday |
| `icims.com` | iCIMS |
| `taleo.net` | Taleo |
| `smartrecruiters.com` | SmartRecruiters |
| `ashbyhq.com` | Ashby |
| unknown | Generic (best-effort field detection) |

---

## 7. Configuration Loading

`config.yaml` is loaded at startup and validated with Pydantic. All sensitive values (API keys, LinkedIn cookies) can alternatively be set as environment variables prefixed `JOBHUNT_` (e.g., `JOBHUNT_LLM__API_KEY`), which take precedence over the file.

---

## 8. Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Fit/success scoring | Algorithmic | Deterministic, fast, cheap, debuggable — LLM won't be calibrated to real hiring data |
| JD + snippet parsing | LLM | Unstructured text → structured fields is where LLM earns its cost |
| Resume output format | JSON → form-filler | No document needed; data feeds directly into Playwright |
| LinkedIn access | Playwright + cookie session | Official API requires partner approval and has limited search scope |
| Concurrency | asyncio + thread pool for Playwright | Single process, no external queue needed for single-user scale |
| Database | SQLite | Simple, zero-infrastructure, swappable via SQLAlchemy |
| LLM interface | Protocol (structural subtyping) | Config-only provider swap, no conditional imports in call sites |
| Resume storage (Tier 1 & 2) | Static YAML files, not DB | User edits resume data directly in a text editor — putting it in a DB would require a UI just to update a bullet point. Files are also version-controllable with git. DB stores only derived data (embeddings cache, usage stats) and is invalidated when the file changes. |
| Resume file format | YAML over JSON and Markdown | JSON requires `\n`-escaped strings for multi-line bullets and has no comment support — poor for human editing. Markdown is natural for prose but has no standard schema for structured fields (tags, dates, IDs), forcing fragile frontmatter conventions. YAML handles both: multi-line bullet content sits naturally in block scalars (`\|`), structured fields (tags, dates, IDs) are first-class, and comments let users annotate entries. `ruamel.yaml` preserves comments and formatting on round-trip if the system ever writes back suggestions. |
| Frontend | Jinja2 + HTMX | Pure Python stack, no build tooling. HTMX handles inline snippet editing and dynamic updates without a JS framework. |

---

## 9. Tooling

### 9.1 Project Management

`uv` is used for all dependency and environment management — no global installs. Dependencies are declared in `pyproject.toml`.

```bash
uv sync          # create venv and install all dependencies
uv run pytest    # run tests inside the managed environment
uv run seekpassion   # start the daemon
```

### 9.2 Code Formatting & Linting

| Tool | Purpose |
|---|---|
| `black` | Opinionated code formatter — enforces consistent style |
| `ruff` | Fast linter covering style, unused imports, and common errors (replaces flake8 + isort) |
| `mypy` | Static type checking |

Run before every commit:
```bash
uv run black . && uv run ruff check . && uv run mypy seekpassion/
```

### 9.2 Testing Approach

Test-driven development: for every module written or changed, tests are written and run before moving on. A change is not complete until its tests pass.

| Layer | Tool | Notes |
|---|---|---|
| Unit | `pytest` | Pure logic — matchers, rankers, parsers, config loading |
| Integration | `pytest` + real SQLite | DB queries, pipeline stages end-to-end |
| Scraper | `pytest` + recorded HTML fixtures | Replay saved ATS pages; no live network calls in CI |
| Submission | `pytest` + Playwright in headless mode | Replay saved ATS form snapshots |

Test fixtures (sample JDs, ATS page snapshots, resume files) live in `tests/fixtures/`.
