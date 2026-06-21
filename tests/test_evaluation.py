from datetime import date, timedelta
from pathlib import Path

import pytest

from seekpassion.config import load_config
from seekpassion.db.models import Job
from seekpassion.db.session import get_session, init_db
from seekpassion.evaluation import jd_parser, matcher, success
from seekpassion.evaluation.profile import load_profile
from seekpassion.evaluation.ranker import run_evaluation

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def profile():
    return load_profile(FIXTURES / "static.yaml", FIXTURES / "pool.yaml")


# --- profile ---

def test_profile_loads(profile):
    assert profile.name == "Test User"
    assert "python" in profile.skills
    assert profile.total_years > 0
    assert profile.education_level == "bachelor"


def test_profile_total_years(profile):
    # exp-001: 2020-01 to 2024-01 = 4 years
    # exp-002: 2016-07 to 2019-12 = ~3.4 years
    assert profile.total_years >= 7.0


# --- jd_parser ---

def test_jd_parser_extracts_skills():
    jd = "We require python and kafka experience. Preferred: spark, docker."
    parsed = jd_parser.parse(jd)
    assert "python" in parsed["required_skills"] or "python" in parsed["preferred_skills"]
    assert "kafka" in parsed["required_skills"] or "kafka" in parsed["preferred_skills"]


def test_jd_parser_extracts_years():
    jd = "You need 5+ years of professional experience in backend systems."
    parsed = jd_parser.parse(jd)
    assert parsed["years_exp"] == 5


def test_jd_parser_extracts_education():
    jd = "A Bachelor's degree in Computer Science or equivalent is required."
    parsed = jd_parser.parse(jd)
    assert parsed["education_req"] == "bachelor"


def test_jd_parser_empty_description():
    parsed = jd_parser.parse("")
    assert parsed["required_skills"] == []
    assert parsed["years_exp"] is None


# --- matcher ---

def test_fit_score_high_match(profile):
    parsed = {
        "required_skills": ["python", "kafka"],
        "preferred_skills": ["spark", "sql"],
        "years_exp": 5,
        "education_req": "bachelor",
    }
    score = matcher.compute_fit_score(profile, parsed, "Senior Software Engineer")
    assert score >= 60.0


def test_fit_score_no_skill_match(profile):
    parsed = {
        "required_skills": ["swift", "kotlin", "react"],
        "preferred_skills": ["angular"],
        "years_exp": 3,
        "education_req": None,
    }
    score = matcher.compute_fit_score(profile, parsed, "iOS Developer")
    assert score < 60.0


def test_fit_score_no_jd_data(profile):
    parsed = {
        "required_skills": [], "preferred_skills": [], "years_exp": None, "education_req": None
    }
    score = matcher.compute_fit_score(profile, parsed, "Engineer")
    assert 0.0 <= score <= 100.0


# --- success estimator ---

def test_success_recent_posting(profile):
    prob = success.compute_success_probability(
        profile, "Senior Software Engineer", date.today(), True, None
    )
    assert prob > 50.0


def test_success_old_posting_penalty(profile):
    old_date = date.today() - timedelta(days=60)
    prob_old = success.compute_success_probability(profile, "Engineer", old_date, False, None)
    prob_new = success.compute_success_probability(profile, "Engineer", date.today(), False, None)
    assert prob_old < prob_new


def test_success_seniority_mismatch_penalty(profile):
    # VP role vs ~7yr candidate → large gap
    prob_vp = success.compute_success_probability(
        profile, "VP of Engineering", date.today(), False, None
    )
    prob_senior = success.compute_success_probability(
        profile, "Senior Engineer", date.today(), False, None
    )
    assert prob_vp < prob_senior


# --- ranker (integration) ---

def test_run_evaluation_updates_status(tmp_path, profile):
    init_db(tmp_path / "test.db")
    session = get_session()

    session.add(Job(
        source="company_board",
        company="Acme",
        title="Senior Software Engineer",
        description="We require python and kafka. 3+ years of experience required. Bachelor's degree.",  # noqa: E501
        job_url="https://acme.com/jobs/1",
        ats_platform="greenhouse",
    ))
    session.commit()

    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "companies: []\n"
        "resume:\n"
        "  static_file: resume/static.yaml\n"
        "  pool_file: resume/pool.yaml\n"
    )
    cfg = load_config(cfg_file)
    count = run_evaluation(profile, cfg, session)
    assert count == 1

    job = session.query(Job).first()
    assert job is not None
    assert job.status == "evaluated"
    assert job.fit_score is not None
    assert job.ranking_score is not None
