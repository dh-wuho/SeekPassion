# SeekPassion

An autonomous job hunting agent that discovers engineering roles, evaluates fit against your resume, and prepares tailored applications — so you can focus on the interviews.

## What it does

1. **Discover** — scrapes configured company career boards (Greenhouse, Lever, Ashby) for new postings, filters to engineering roles at your seniority level
2. **Evaluate** — scores each job on fit (skill overlap, experience, title match, education) and success probability (seniority gap, posting age, remote compatibility), then ranks them
3. **Tailor** *(coming soon)* — polishes resume snippets per job using an LLM, aligned to each JD's language and keywords
4. **Submit** *(coming soon)* — auto-fills application forms via Playwright, with two user review gates before anything is submitted

## Quickstart

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
git clone git@github.com:dh-wuho/SeekPassion.git
cd SeekPassion
uv sync
```

Edit `config.yaml` to add your target companies and point to your resume files:

```yaml
companies:
  - name: Anthropic
    url: https://boards.greenhouse.io/anthropic
  - name: Stripe
    url: https://jobs.lever.co/stripe

resume:
  static_file: resume/static.yaml   # contact, education, certifications
  pool_file: resume/pool.yaml        # experience and project entries

discovery:
  domains: [engineering]
  min_years_required: 4
```

Then run:

```bash
uv run sp discover    # scrape all configured companies
uv run sp evaluate    # score and rank new jobs
uv run sp list        # show top results
```

## Resume files

SeekPassion uses two YAML files — edit them directly, no UI needed.

**`resume/static.yaml`** — never changes across applications (contact info, education, certifications)

**`resume/pool.yaml`** — your full experience and project library, tagged for retrieval:

```yaml
experiences:
  - id: exp-001
    title: Senior Software Engineer
    company: Acme Corp
    start: "2021-03"
    end: "2024-01"
    tags: [python, kafka, distributed-systems, backend]
    bullets:
      - Reduced P99 latency by 40% by redesigning cache invalidation strategy
      - Led migration of monolith to microservices serving 50M req/day
```

## Configuration

| Setting | Description | Default |
|---|---|---|
| `companies` | List of target companies + careers URLs | `[]` |
| `discovery.domains` | Job domains to fetch (`engineering`, `sales`, etc.) | `[engineering]` |
| `discovery.min_years_required` | Min years required for generic-title roles | `4` |
| `discovery.max_job_age_weeks` | Ignore postings older than this | `4` |
| `fit_weight` | Weight of fit score in ranking | `0.6` |
| `success_weight` | Weight of success probability in ranking | `0.4` |
| `min_fit_score` | Minimum fit score to show in list | `40` |

## Development

```bash
uv run pytest          # run tests
uv run black .         # format
uv run ruff check .    # lint
uv run mypy seekpassion/  # type check
```

## Supported ATS platforms

Discovery (scraping): **Greenhouse**, **Lever**, **Ashby**

Submission *(coming soon)*: Greenhouse, Lever, Workday, iCIMS, Taleo, SmartRecruiters, Ashby

## Roadmap

- [ ] LLM-based JD parser (replaces heuristic)
- [ ] LinkedIn job search
- [ ] Resume tailoring pipeline
- [ ] Phase 1 review web UI (FastAPI + HTMX)
- [ ] Automated form submission (Playwright)
- [ ] Email notifications
