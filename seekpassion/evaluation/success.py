from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from seekpassion.evaluation.profile import CandidateProfile

_SENIORITY_KEYWORDS = {
    "intern": -2, "junior": -1, "associate": -1,
    "mid": 0, "senior": 1, "staff": 2, "principal": 2, "lead": 2,
    "manager": 2, "director": 3, "vp": 4, "head": 3,
}


def _seniority(title: str) -> int:
    t = title.lower()
    for kw, level in _SENIORITY_KEYWORDS.items():
        if kw in t:
            return level
    return 0


def _candidate_seniority(profile: CandidateProfile) -> int:
    if profile.total_years >= 10:
        return 2
    if profile.total_years >= 5:
        return 1
    if profile.total_years >= 2:
        return 0
    return -1


def _posting_age_penalty(date_posted: Optional[date]) -> float:
    if date_posted is None:
        return 0.0
    age_days = (datetime.now(timezone.utc).date() - date_posted).days
    if age_days <= 14:
        return 0.0
    return min(20.0, (age_days - 14) * 0.5)


def _seniority_penalty(profile: CandidateProfile, job_title: str) -> float:
    job_level = _seniority(job_title)
    candidate_level = _candidate_seniority(profile)
    gap = abs(job_level - candidate_level)
    return min(30.0, gap * 12.0)


def _remote_bonus(job_remote: bool, job_location: Optional[str]) -> float:
    if job_remote:
        return 5.0
    return 0.0


def compute_success_probability(
    profile: CandidateProfile,
    job_title: str,
    date_posted: Optional[date],
    job_remote: bool,
    job_location: Optional[str],
) -> float:
    base = 65.0
    score = base
    score -= _posting_age_penalty(date_posted)
    score -= _seniority_penalty(profile, job_title)
    score += _remote_bonus(job_remote, job_location)
    return round(max(0.0, min(100.0, score)), 1)
