from __future__ import annotations

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "engineering": [
        "engineer", "developer", "architect", "sre", "devops", "platform",
        "infrastructure", "backend", "frontend", "fullstack", "full-stack",
        "ml", "machine learning", "data scientist", "data engineer",
        "researcher", "scientist", "security engineer", "software",
    ],
    "sales": [
        "account executive", "sales", "business development", "revenue",
        "account manager", "solutions engineer", "sales engineer",
    ],
    "recruiter": [
        "recruiter", "talent acquisition", "talent partner", "sourcer",
        "hr ", "human resources", "people ops", "people partner",
    ],
    "finance": [
        "accountant", "accounting", "finance", "financial", "controller",
        "fp&a", "treasury", "tax", "audit",
    ],
    "marketing": [
        "marketing", "growth", "content", "brand", "demand generation",
        "seo", "social media", "communications",
    ],
    "design": [
        "designer", "ux", "ui ", "product design", "visual design",
        "creative", "illustrator",
    ],
    "legal": [
        "legal", "counsel", "attorney", "compliance", "privacy", "policy",
    ],
    "product": [
        "product manager", "program manager", "project manager", "scrum",
    ],
    "operations": [
        "operations", "ops", "supply chain", "logistics", "facilities",
    ],
}

_SENIOR_KEYWORDS = ["senior", "staff", "principal", "lead", "architect", "fellow"]
_JUNIOR_KEYWORDS = ["intern", "junior", "associate", "entry-level", "entry level", "new grad"]


def classify_domain(title: str) -> str:
    t = title.lower()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return domain
    return "unknown"


def _has_senior_signal(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in _SENIOR_KEYWORDS)


def _has_junior_signal(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in _JUNIOR_KEYWORDS)


def should_include(
    title: str,
    allowed_domains: list[str],
    title_exclude: list[str],
) -> tuple[bool, bool]:
    """
    Returns (include, generic_title).
    generic_title=True means no seniority signal — years filter applies later.
    """
    t = title.lower()

    if any(kw.lower() in t for kw in title_exclude):
        return False, False

    domain = classify_domain(title)
    if domain not in allowed_domains:
        return False, False

    if _has_junior_signal(title):
        return False, False

    generic = not _has_senior_signal(title)
    return True, generic
