from __future__ import annotations

import re
from typing import Optional

from seekpassion.evaluation.profile import CandidateProfile

_EDU_RANK = {"high_school": 0, "bachelor": 1, "master": 2, "phd": 3}

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


def _skill_score(candidate_skills: set[str], required: list[str], preferred: list[str]) -> float:
    """Weighted Jaccard: required counts 2x, preferred 1x."""
    if not required and not preferred:
        return 50.0
    weighted_union = len(required) * 2 + len(preferred)
    weighted_intersection = (
        sum(2 for s in required if s.lower() in candidate_skills)
        + sum(1 for s in preferred if s.lower() in candidate_skills)
    )
    if weighted_union == 0:
        return 50.0
    return min(100.0, (weighted_intersection / weighted_union) * 100)


def _experience_score(candidate_years: float, required_years: Optional[int]) -> float:
    if required_years is None:
        return 70.0
    delta = candidate_years - required_years
    if delta >= 0:
        return min(100.0, 80.0 + delta * 2)
    # Under-qualified: decay 8 points per year gap
    return max(0.0, 80.0 + delta * 8)


def _title_score(candidate_experiences: list, job_title: str) -> float:
    job_tokens = set(re.findall(r"\w+", job_title.lower()))
    best = 0.0
    for exp in candidate_experiences:
        tokens = set(re.findall(r"\w+", exp.title.lower()))
        overlap = len(tokens & job_tokens) / max(len(tokens | job_tokens), 1)
        best = max(best, overlap)
    return best * 100


def _education_score(candidate_level: str, required_level: Optional[str]) -> float:
    if not required_level:
        return 100.0
    candidate_rank = _EDU_RANK.get(candidate_level, 0)
    required_rank = _EDU_RANK.get(required_level, 1)
    return 100.0 if candidate_rank >= required_rank else 0.0


def compute_fit_score(profile: CandidateProfile, jd_parsed: dict, job_title: str) -> float:
    skill = _skill_score(
        profile.skills,
        jd_parsed.get("required_skills", []),
        jd_parsed.get("preferred_skills", []),
    )
    experience = _experience_score(profile.total_years, jd_parsed.get("years_exp"))
    title = _title_score(profile.experiences, job_title)
    education = _education_score(profile.education_level, jd_parsed.get("education_req"))

    score = skill * 0.50 + experience * 0.30 + title * 0.10 + education * 0.10
    return round(score, 1)
