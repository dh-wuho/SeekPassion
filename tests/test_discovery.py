from seekpassion.db.models import Job
from seekpassion.db.session import get_session, init_db
from seekpassion.discovery.base import RawJob, detect_ats
from seekpassion.discovery.deduplicator import upsert_jobs
from seekpassion.discovery.filters import classify_domain, should_include


def test_detect_ats_greenhouse():
    assert detect_ats("https://boards.greenhouse.io/anthropic") == "greenhouse"


def test_detect_ats_lever():
    assert detect_ats("https://jobs.lever.co/notion") == "lever"


def test_detect_ats_ashby():
    assert detect_ats("https://jobs.ashbyhq.com/acme") == "ashby"


def test_detect_ats_unknown():
    assert detect_ats("https://careers.somecompany.com/jobs") == "unknown"


# --- domain classification ---

def test_classify_engineering():
    assert classify_domain("Senior Software Engineer") == "engineering"
    assert classify_domain("Staff ML Engineer") == "engineering"
    assert classify_domain("Data Scientist") == "engineering"


def test_classify_sales():
    assert classify_domain("Account Executive, AI Native") == "sales"


def test_classify_recruiter():
    assert classify_domain("Technical Recruiter") == "recruiter"


def test_classify_finance():
    assert classify_domain("Senior Manager, Corporate Accounting") == "finance"


# --- should_include ---

def test_include_senior_engineering():
    include, generic = should_include("Senior Software Engineer", ["engineering"], [])
    assert include is True
    assert generic is False


def test_include_generic_engineering():
    include, generic = should_include("Software Engineer", ["engineering"], [])
    assert include is True
    assert generic is True


def test_exclude_junior():
    include, _ = should_include("Junior Software Engineer", ["engineering"], [])
    assert include is False


def test_exclude_intern():
    include, _ = should_include("Software Engineering Intern", ["engineering"], [])
    assert include is False


def test_exclude_wrong_domain():
    include, _ = should_include("Account Executive", ["engineering"], [])
    assert include is False


def test_exclude_custom_keyword():
    include, _ = should_include(  # noqa: E501
        "Senior Software Engineer, Sales Tooling", ["engineering"], ["sales tooling"]
    )
    assert include is False


# --- deduplicator ---

def test_upsert_jobs_inserts_new(tmp_path):
    init_db(tmp_path / "test.db")
    session = get_session()

    raw = [
        RawJob(company="Acme", title="Senior Engineer", job_url="https://example.com/1", ats_platform="greenhouse"),  # noqa: E501
        RawJob(company="Acme", title="Staff Engineer", job_url="https://example.com/2", ats_platform="greenhouse"),  # noqa: E501
    ]
    inserted, skipped, filtered = upsert_jobs(raw, session)
    assert inserted == 2
    assert skipped == 0
    assert filtered == 0
    assert session.query(Job).count() == 2


def test_upsert_filters_non_engineering(tmp_path):
    init_db(tmp_path / "test.db")
    session = get_session()

    raw = [
        RawJob(company="Acme", title="Senior Software Engineer", job_url="https://example.com/1", ats_platform="greenhouse"),  # noqa: E501
        RawJob(company="Acme", title="Account Executive", job_url="https://example.com/2", ats_platform="greenhouse"),  # noqa: E501
        RawJob(company="Acme", title="Technical Recruiter", job_url="https://example.com/3", ats_platform="greenhouse"),  # noqa: E501
    ]
    inserted, skipped, filtered = upsert_jobs(raw, session, allowed_domains=["engineering"])
    assert inserted == 1
    assert filtered == 2


def test_upsert_filters_junior(tmp_path):
    init_db(tmp_path / "test.db")
    session = get_session()

    raw = [
        RawJob(company="Acme", title="Junior Software Engineer", job_url="https://example.com/1", ats_platform="greenhouse"),  # noqa: E501
    ]
    inserted, skipped, filtered = upsert_jobs(raw, session)
    assert inserted == 0
    assert filtered == 1


def test_upsert_marks_generic_title(tmp_path):
    init_db(tmp_path / "test.db")
    session = get_session()

    raw = [
        RawJob(company="Acme", title="Software Engineer", job_url="https://example.com/1", ats_platform="greenhouse"),  # noqa: E501
    ]
    upsert_jobs(raw, session)
    job = session.query(Job).first()
    assert job is not None
    assert job.generic_title is True


def test_upsert_jobs_skips_duplicates(tmp_path):
    init_db(tmp_path / "test.db")
    session = get_session()

    raw = [RawJob(company="Acme", title="Senior Engineer", job_url="https://example.com/1", ats_platform="greenhouse")]  # noqa: E501
    upsert_jobs(raw, session)
    inserted, skipped, filtered = upsert_jobs(raw, session)
    assert inserted == 0
    assert skipped == 1
    assert session.query(Job).count() == 1


def test_upsert_sets_status_new(tmp_path):
    init_db(tmp_path / "test.db")
    session = get_session()

    raw = [RawJob(company="X", title="Senior Engineer", job_url="https://x.com/j1", ats_platform="lever")]  # noqa: E501
    upsert_jobs(raw, session)
    job = session.query(Job).first()
    assert job is not None
    assert job.status == "new"
