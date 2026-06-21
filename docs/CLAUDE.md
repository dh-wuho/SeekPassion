# CLAUDE.md — Implementation Principles

## Philosophy
Test-driven, effective, and concise. Write the simplest code that passes the tests. No over-engineering, no speculative abstractions, no unnecessary comments.

## Project Management
- Use `uv` for all dependency and environment management. Never install packages globally.
- All tool runs go through `uv run` (e.g. `uv run pytest`, `uv run black .`).
- Dependencies are declared in `pyproject.toml`.

## Code Style
- Run `uv run black . && uv run ruff check . && uv run mypy seekpassion/` before finishing any file.
- Type hints on every function signature — mypy must pass clean.
- No comments unless the WHY is non-obvious. Never explain what the code does; well-named identifiers do that.
- No docstrings unless the interface is consumed externally.

## Test-Driven Development
- Write tests before or alongside implementation — not after.
- Every file changed must have corresponding tests written and passing before moving on.
- A change is not complete until its tests pass.
- Use real SQLite for integration tests — no mocking the database.
- Scraper and submission tests use recorded HTML fixtures, not live network calls.

## Architecture
- Follow `design.md` for all structural decisions. Do not introduce abstractions beyond what the design specifies.
- All LLM calls go through the `LLMProvider` protocol in `llm/base.py` — never call a provider SDK directly from business logic.
- Async/await throughout — no blocking I/O on the event loop. Use the thread pool for Playwright.
- Do not add error handling for scenarios that cannot happen. Trust internal guarantees; validate only at system boundaries (config load, scraper output, LLM responses).

---

## Change Log

After each implementation session, append an entry below with: what changed, any decisions made, and — most importantly — uncertainties that need user review before proceeding.

### Format
```
### YYYY-MM-DD — <module or feature>
**Changed:** ...
**Decided:** ...
**Uncertainties (needs review):**
- [ ] ...
```

### Log

### 2026-06-20 — Discovery + Evaluation (initial implementation)

**Changed:**
- `pyproject.toml` — project setup with `uv`, hatchling build, all deps
- `config.yaml`, `resume/static.yaml`, `resume/pool.yaml` — sample data
- `seekpassion/config.py` — Pydantic config loader
- `seekpassion/db/models.py` + `session.py` — SQLAlchemy ORM (jobs, tailored_applications, llm_suggestions)
- `seekpassion/discovery/base.py` — `RawJob` dataclass, `Scraper` protocol, `detect_ats()`
- `seekpassion/discovery/company_board.py` — `GreenhouseScraper`, `LeverScraper`, `AshbyScraper`, `build_scraper()`
- `seekpassion/discovery/deduplicator.py` — `upsert_jobs()` keyed on `job_url`
- `seekpassion/evaluation/profile.py` — loads Tier 1 + Tier 2 YAML into `CandidateProfile`
- `seekpassion/evaluation/jd_parser.py` — heuristic parser (skills, years, education, responsibilities)
- `seekpassion/evaluation/matcher.py` — fit score: skill overlap (50%) + experience (30%) + title (10%) + education (10%)
- `seekpassion/evaluation/success.py` — success probability: base 65 − posting age penalty − seniority gap + remote bonus
- `seekpassion/evaluation/ranker.py` — runs evaluation on all `new` jobs, writes scores + sets `status=evaluated`
- `seekpassion/main.py` — CLI: `discover`, `evaluate`, `list`
- `tests/` — 22 tests, all passing; linter clean

**Decided:**
- JD parser is heuristic (no LLM) — functional placeholder; LLM version replaces it later
- LinkedIn scraper skipped (Playwright out of scope for this phase)
- Workday/iCIMS/Taleo/SmartRecruiters scrapers skipped — no public JSON API; need HTML parsing

**Uncertainties (needs review):**
- [ ] Notion's Lever URL returned 404 — is `jobs.lever.co/notion` the right slug? Check their actual careers URL
- [ ] Fit scores are modest (43–54 range on Anthropic jobs with a Python/Kafka background) — heuristic skill matching without LLM produces lower scores because it only matches exact known skills. Is this acceptable until LLM parser is wired up, or should the score scale be adjusted?
- [ ] `success_probability` is 65 for most jobs (base rate, no posting age penalty, no seniority gap) — this will differentiate more once older postings accumulate. Acceptable for now?
- [ ] Workday/iCIMS/Taleo scrapers are not implemented — any priority companies using those platforms?

### 2026-06-20 — Discovery filters (domain + seniority + min years)

**Changed:**
- `seekpassion/config.py` — added `domains`, `title_exclude`, `min_years_required` to `DiscoveryConfig`
- `seekpassion/discovery/filters.py` — new module: `classify_domain()`, `should_include()` with domain + junior/senior/generic classification
- `seekpassion/discovery/deduplicator.py` — applies title filter before insert; returns `(inserted, skipped, filtered)` tuple; sets `generic_title` flag
- `seekpassion/db/models.py` — added `generic_title` boolean column to `Job`
- `seekpassion/evaluation/ranker.py` — drops generic-title jobs where `years_exp < min_years_required` during evaluation
- `seekpassion/main.py` — passes filter config to `upsert_jobs`, shows filtered count in output
- `config.yaml` — added `domains: [engineering]`, `min_years_required: 4`
- `requirements.md`, `design.md` — updated to document filter logic
- Tests: 35 passing, linter clean

**Result:** 373 Anthropic postings → 183 filtered out → 190 engineering jobs stored → 189 evaluated

**Uncertainties (needs review):**
- [ ] "Anthropic Fellows Program" passes the engineering filter — is this correct or should fellowship programs be excluded?
- [ ] Generic-title jobs with no `years_exp` in the JD always pass through — acceptable?
