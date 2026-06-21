# SeekPassion Agent — Requirements

## Overview

An autonomous agent that discovers job openings, evaluates fit against a candidate's resume, ranks opportunities by match quality and estimated success rate, tailors the resume to each job description, and auto-fills applications.

---

## 1. Job Discovery

### 1.1 Predefined Company Job Boards
- Maintain a configurable list of target companies (name + careers page URL or known ATS endpoint).
- Scrape or poll each company's careers page on a defined schedule (e.g., daily).
- Detect new postings since last scan and avoid re-processing already-seen jobs.
- Support common ATS platforms: Greenhouse, Lever, Workday, iCIMS, Taleo, SmartRecruiters, Ashby.
- Store raw job data: title, description, location, salary range (if listed), date posted, application URL.
- Filter postings at scrape time before writing to DB:
  - **Domain filter** — classify each job title into a domain (engineering, sales, recruiter, finance, marketing, design, legal, etc.) and only store jobs whose domain matches `discovery.domains`. Unrecognised domains are excluded by default.
  - **Seniority filter** — two-step:
    1. If title contains an explicit senior keyword (senior, staff, principal, lead, architect) → include.
    2. If title is generic (no seniority signal) → defer: include provisionally and apply `discovery.min_years_required` after JD parsing during evaluation.
    3. If title contains a junior keyword (intern, junior, associate, entry-level) → exclude immediately.

### 1.2 LinkedIn Job Search
- Authenticate with LinkedIn via cookie-based session (Playwright).
- Accept configurable search parameters: keywords, location, job type (full-time/contract), experience level, remote preference.
- Paginate through results and extract job details.
- Use conservative, randomized delays between requests to mimic human browsing pace (configurable; default targets ~100 jobs discovered per 24-hour cycle, roughly one request every 15 minutes).
- If LinkedIn returns a CAPTCHA or temporary block, log the event, pause the LinkedIn module, and continue with company career board discovery until the next cycle.
- Deduplicate across LinkedIn and company board sources.

---

## 2. Job Evaluation & Ranking

### 2.1 Resume Parsing
- Accept resume as a PDF or DOCX file.
- Extract structured data: skills, experience (role, company, duration), education, certifications, projects.
- Build a candidate profile that can be compared against job requirements.

### 2.2 Job–Resume Matching
- Parse each job description to extract: required skills, preferred skills, years of experience, education requirements, responsibilities.
- Score each job on multiple dimensions:
  - **Skill match** — overlap between candidate skills and job requirements.
  - **Experience match** — years and seniority level alignment.
  - **Title/role match** — similarity of target role to past roles.
  - **Education match** — degree and field requirements vs. candidate background.
- Produce a composite **fit score** (0–100).

### 2.3 Success Rate Estimation
- Factor in signals beyond raw fit:
  - Company size and typical hiring bar.
  - Seniority gap (over/under-qualified risk).
  - Time posted (older postings may be filled).
  - Location / remote compatibility.
- Output an estimated **success probability** (0–100%) per job, distinct from fit score.

### 2.4 Ranking & Output
- Rank all discovered jobs by a weighted combination of fit score and success probability.
- Expose configurable weights (default: 60% fit, 40% success rate).
- Present a ranked list with: rank, job title, company, fit score, success rate, key matching strengths, key gaps.
- Support filtering: by minimum fit score, by remote-only, by salary floor, by location.

---

## 3. Resume Tailoring

### 3.1 Resume Data Model (Three Tiers)

**Tier 1 — Static file (user-maintained)**
- A single file containing information that never changes across applications: name, phone, email, address, education, certifications.
- Read-only to the system; never modified by tailoring or LLM.

**Tier 2 — Base pool file (user-maintained, LLM-advisable)**
- A single file containing the user's full set of experience entries and projects — typically more entries than any one application will use.
- This is the authoritative source for all tailoring; all polished snippets derive from these base descriptions.
- LLM may suggest an update to a base entry if a polished variant produced during tailoring is clearly stronger than the original — presented to the user for approval, never applied automatically.
- User edits this file directly to add, remove, or update entries over time.
- Each entry carries metadata tags (e.g., technologies, themes like `latency`, `ml`, `infra`, `leadership`) to support retrieval.

**Tier 3 — Per-application records (system-generated)**
- For each job application, the system stores a record containing the selected and polished experience/project entries for that specific job.
- Static information (Tier 1) is excluded — it is merged only at display/review time.
- Used for Phase 1 web UI review, email review in Phase 2, and future reference.
- Stores both the original base text and the polished text side-by-side for auditability.

### 3.2 Per-Job Tailoring Pipeline
- Triggered for each job at or above a configurable fit score threshold.
- **Step 1 — Select:** retrieve the top-N most relevant dynamic snippets from the pool using embedding similarity or LLM ranking against the JD's required skills and responsibilities.
- **Step 2 — Polish:** LLM rewrites only the selected snippets with two goals in parallel:
  - **JD alignment** — mirror the JD's language and surface keywords the base entry implies but doesn't state explicitly.
  - **ATS / AI screener compatibility** — maximize the likelihood of passing automated resume screening:
    - Use exact keyword forms from the JD (ATS systems match literals, not synonyms).
    - Lead bullet points with strong action verbs followed by quantifiable outcomes.
    - Avoid tables, columns, graphics, or unusual formatting that ATS parsers misread.
    - Prefer plain, conventional phrasing over creative language that AI classifiers may score lower.
    - Ensure skill terms appear in context, not just in a skills list, as AI screeners weight in-context mentions more heavily.
  - No new facts added; only reframing of existing experience.
- Static and semi-static components are passed through unchanged (skills list may be reordered).

### 3.3 Output Format
- Tailored resume is stored as structured data (JSON) linked to the job record — no document export.
- This structured payload feeds directly into the application form-filler (section 4).
- Each tailored record stores: which snippets were selected, the original text, and the polished text, for user review and auditability.

---

## 4. Automated Application Submission

All submissions require two explicit user review gates before anything is submitted.

### 4.1 Phase 1 — Daily Preparation & Review (Web UI)
- Each day, pre-compute and prepare tailored resume data for up to 50 top-ranked jobs.
- Present all 50 applications in a local web UI: for each job show the selected snippets, polished text, fit score, success rate, and key gaps.
- User reviews and optionally edits any prepared application, then confirms the batch to proceed to submission.
- No browser automation or form-filling starts until the user confirms Phase 1.

### 4.2 Phase 2 — Batched Form-Fill & Submission
- After Phase 1 confirmation, open `submission_batch_size` browser tabs concurrently using Playwright.
- Auto-fill each application form: name, email, phone, address, LinkedIn URL, portfolio/GitHub URL, and tailored resume upload.
- Map candidate profile fields to ATS-specific form layouts (Greenhouse, Lever, Workday, iCIMS, Taleo, SmartRecruiters, Ashby).
- Stop at each application's own final review/confirm step — do not click the final submit button.
- Send an email notification to the user with a summary of the pre-filled batch ready for review.
- Once the user confirms, submit the batch, then immediately start the next batch.
- Repeat until `daily_application_limit` total submissions are completed for the day.

### 4.3 Submission Tracking
- Record each application: job, company, date submitted, resume variant used, application URL, status.
- Track status updates (applied → interview → offer → rejected) via manual update.

---

## 5. Persistence & Storage

- All job records, scores, resume variants, and application history stored in a local database (SQLite for simplicity, swappable).
- Incremental scans: only process new jobs discovered since last run.
- Configurable data retention policy.

---

## 6. Configuration

| Setting | Description | Default |
|---|---|---|
| `companies` | List of target companies + careers URLs | `[]` |
| `linkedin.keywords` | Search terms for LinkedIn | `[]` |
| `linkedin.location` | Target location(s) | `""` |
| `linkedin.remote_only` | Filter to remote jobs | `false` |
| `discovery.max_job_age_weeks` | Ignore postings older than this many weeks at scrape time | `4` |
| `discovery.domains` | Job domains to include (`engineering`, `sales`, `recruiter`, `finance`, `marketing`, `design`, `legal`) | `[engineering]` |
| `discovery.title_exclude` | Additional title keywords to always exclude regardless of domain | `[]` |
| `discovery.min_years_required` | For generic titles with no seniority signal, exclude jobs requiring fewer years than this | `4` |
| `linkedin.request_delay_min` | Minimum seconds between LinkedIn requests | `600` (10 min) |
| `linkedin.request_delay_max` | Maximum seconds between LinkedIn requests | `1200` (20 min) |
| `fit_weight` | Weight of fit score in ranking | `0.6` |
| `success_weight` | Weight of success probability in ranking | `0.4` |
| `min_fit_score` | Minimum score to include in output | `50` |
| `daily_application_limit` | Max applications to prepare and submit per day | `50` |
| `submission_batch_size` | Number of concurrent browser tabs per submission batch | `10` |
| `notification_email` | Email address to notify when a submission batch is ready for review | required |
| `resume.static_file` | Path to Tier 1 static info file (education, contact, etc.) | required |
| `resume.pool_file` | Path to Tier 2 base experience/projects pool file | required |
| `snippet_select_n` | Number of dynamic snippets to select per job | `5` |
| `llm.provider` | LLM provider (`anthropic`, `openai`, `gemini`, `mistral`) | `anthropic` |
| `llm.model` | Model name for the selected provider | provider default |
| `llm.api_key` | API key for the selected provider | required |
| `llm.base_url` | Override API base URL (for proxies or self-hosted endpoints) | provider default |

---

## 7. Non-Functional Requirements

- **Runtime** — runs as a continuous background daemon (24/7); discovery, evaluation, and submission phases operate on independent schedules within the same process.
- **Privacy** — credentials and personal data stored locally; no third-party data sharing.
- **Rate limiting** — polite scraping with configurable delays; LinkedIn session must not trigger lockout.
- **Observability** — structured logs per run; summary report after each scan.
- **Tech stack** — Python; FastAPI for the local web UI backend; Playwright (Python SDK) for browser automation; SQLite via SQLAlchemy for persistence.
- **Modularity** — job discovery, evaluation, tailoring, and submission are independent modules with clean interfaces.
- **LLM backend** — pluggable provider abstraction; the system must support any API-key-based LLM provider (e.g., Anthropic, OpenAI, Google Gemini, Mistral). Provider, model, and API key are all configurable. All LLM calls go through a single interface so switching providers requires only a config change, not code changes.
- **Testability** — each module independently testable; fixture data for offline development.

---

## 8. Out of Scope (v1)

- Email parsing for status tracking (manual status updates only in v1).
- Mobile app or browser extension.
- Multi-candidate / team use.
- Platforms other than LinkedIn for job discovery (Indeed, Glassdoor, etc.) — add in v2.
- Phone screen scheduling automation.
- OAuth-based LLM authentication — only API-key providers supported in v1.

---

## 9. Open Questions
