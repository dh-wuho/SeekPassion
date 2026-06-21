from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ruamel.yaml import YAML


@dataclass
class Experience:
    id: str
    title: str
    company: str
    tags: list[str]
    start: str
    end: Optional[str]  # None means current


@dataclass
class CandidateProfile:
    name: str
    skills: set[str]
    experiences: list[Experience]
    total_years: float
    education_level: str  # high_school | bachelor | master | phd


def _education_level(edu_list: list[dict]) -> str:
    levels = {"phd": 4, "master": 3, "bachelor": 2, "high_school": 1}
    best = "high_school"
    best_val = 1
    for edu in edu_list:
        degree = edu.get("degree", "").lower()
        if "phd" in degree or "doctor" in degree:
            if levels["phd"] > best_val:
                best, best_val = "phd", levels["phd"]
        elif "master" in degree or "m.s" in degree or "msc" in degree:
            if levels["master"] > best_val:
                best, best_val = "master", levels["master"]
        elif "bachelor" in degree or "b.s" in degree or "b.a" in degree:
            if levels["bachelor"] > best_val:
                best, best_val = "bachelor", levels["bachelor"]
    return best


def _years_from_experience(experiences: list[Experience]) -> float:
    total_months = 0
    now = datetime.now(timezone.utc)
    for exp in experiences:
        try:
            start_dt = datetime.strptime(exp.start, "%Y-%m")
        except ValueError:
            continue
        if exp.end:
            try:
                end_dt = datetime.strptime(exp.end, "%Y-%m")
            except ValueError:
                end_dt = now
        else:
            end_dt = now
        total_months += (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    return round(total_months / 12, 1)


def load_profile(static_path: Path | str, pool_path: Path | str) -> CandidateProfile:
    yaml = YAML()
    with open(static_path) as f:
        static = yaml.load(f)
    with open(pool_path) as f:
        pool = yaml.load(f)

    experiences: list[Experience] = []
    all_tags: set[str] = set()

    for exp in pool.get("experiences", []):
        tags = [t.lower() for t in exp.get("tags", [])]
        all_tags.update(tags)
        experiences.append(
            Experience(
                id=exp["id"],
                title=exp["title"],
                company=exp["company"],
                tags=tags,
                start=str(exp.get("start", "")),
                end=str(exp.get("end", "")) if exp.get("end") else None,
            )
        )

    for proj in pool.get("projects", []):
        tags = [t.lower() for t in proj.get("tags", [])]
        all_tags.update(tags)

    edu_list = static.get("education", [])
    return CandidateProfile(
        name=static.get("name", ""),
        skills=all_tags,
        experiences=experiences,
        total_years=_years_from_experience(experiences),
        education_level=_education_level(edu_list),
    )
