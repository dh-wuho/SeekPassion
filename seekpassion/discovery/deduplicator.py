from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from seekpassion.db.models import Job
from seekpassion.discovery.base import RawJob
from seekpassion.discovery.filters import should_include

logger = logging.getLogger(__name__)


def upsert_jobs(
    raw_jobs: list[RawJob],
    session: Session,
    allowed_domains: list[str] | None = None,
    title_exclude: list[str] | None = None,
) -> tuple[int, int, int]:
    """
    Insert new jobs after applying domain + seniority filters.
    Returns (inserted, skipped_duplicate, filtered_out).
    """
    if allowed_domains is None:
        allowed_domains = ["engineering"]
    if title_exclude is None:
        title_exclude = []

    existing_urls: set[str] = {url for (url,) in session.query(Job.job_url).all()}

    inserted = 0
    skipped = 0
    filtered = 0

    for raw in raw_jobs:
        if raw.job_url in existing_urls:
            skipped += 1
            continue

        include, generic = should_include(raw.title, allowed_domains, title_exclude)
        if not include:
            filtered += 1
            continue

        job = Job(
            source=raw.source,
            company=raw.company,
            title=raw.title,
            description=raw.description,
            location=raw.location,
            remote=raw.remote,
            date_posted=raw.date_posted,
            job_url=raw.job_url,
            ats_platform=raw.ats_platform,
            generic_title=generic,
            status="new",
        )
        session.add(job)
        existing_urls.add(raw.job_url)
        inserted += 1

    session.commit()
    logger.info(
        "Deduplicator: %d inserted, %d duplicates, %d filtered out",
        inserted, skipped, filtered,
    )
    return inserted, skipped, filtered
