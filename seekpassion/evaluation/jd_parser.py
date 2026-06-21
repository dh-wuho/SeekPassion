"""
Heuristic JD parser — extracts structured fields from raw job description text
without an LLM. Accuracy is lower than an LLM-based approach; this is a
functional placeholder until the LLM pipeline is wired up.
"""
from __future__ import annotations

import re
from typing import Optional

KNOWN_SKILLS = {
    "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
    "ruby", "scala", "kotlin", "swift", "r", "matlab",
    "sql", "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "kafka", "spark", "hadoop", "airflow", "dbt", "flink",
    "aws", "gcp", "azure", "terraform", "kubernetes", "docker", "helm",
    "django", "fastapi", "flask", "react", "vue", "angular", "node.js",
    "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy",
    "git", "ci/cd", "linux", "bash", "rest", "graphql", "grpc",
    "machine learning", "deep learning", "nlp", "computer vision",
    "distributed systems", "microservices", "latency", "infra", "backend",
    "frontend", "full-stack", "data engineering", "data science", "mlops",
    "llm", "rag", "vector database",
}

_EDU_PATTERNS = {
    "phd": re.compile(r"\bph\.?d\b|\bdoctorate\b", re.IGNORECASE),
    "master": re.compile(r"\bmaster'?s?\b|\bm\.s\.?\b|\bmsc\b", re.IGNORECASE),
    "bachelor": re.compile(
        r"\bbachelor'?s?\b|\bb\.s\.?\b|\bb\.a\.?\b|\bundergraduate\b", re.IGNORECASE
    ),
}

_YEARS_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:–|-|to)?\s*(\d+)?\s*\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience",
    re.IGNORECASE,
)

_REMOTE_PATTERN = re.compile(r"\bremote\b", re.IGNORECASE)


def parse(description: str) -> dict:
    text = description or ""

    # Skills: case-insensitive substring match against known skill list
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    lower = text.lower()
    for skill in KNOWN_SKILLS:
        if skill in lower:
            # Heuristic: skills near "required"/"must" → required, else preferred
            pattern = re.compile(re.escape(skill), re.IGNORECASE)
            for m in pattern.finditer(text):
                window = text[max(0, m.start() - 120) : m.start()].lower()
                if any(w in window for w in ("require", "must", "need", "essential")):
                    if skill not in required_skills:
                        required_skills.append(skill)
                    break
                else:
                    if skill not in preferred_skills and skill not in required_skills:
                        preferred_skills.append(skill)
                    break

    # Years of experience
    years_exp: Optional[int] = None
    match = _YEARS_PATTERN.search(text)
    if match:
        years_exp = int(match.group(1))

    # Education requirement
    education_req: Optional[str] = None
    for level, pattern in _EDU_PATTERNS.items():
        if pattern.search(text):
            education_req = level
            break

    # Responsibilities: lines starting with action verbs or bullet chars
    responsibilities: list[str] = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("•·-–*").strip()
        if len(stripped) > 20 and re.match(r"^[A-Z][a-z]", stripped):
            responsibilities.append(stripped)
    responsibilities = responsibilities[:10]

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "years_exp": years_exp,
        "education_req": education_req,
        "responsibilities": responsibilities,
    }
