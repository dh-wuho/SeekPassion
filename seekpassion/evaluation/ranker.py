from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from seekpassion.config import Config
from seekpassion.db.models import Job
from seekpassion.evaluation import jd_parser, matcher, success
from seekpassion.evaluation.profile import CandidateProfile

logger = logging.getLogger(__name__)


def run_evaluation(profile: CandidateProfile, config: Config, session: Session) -> int:
    """Evaluate all 'new' jobs. Returns count of jobs evaluated."""
    new_jobs: list[Job] = session.query(Job).filter(Job.status == "new").all()
    evaluated = 0

    min_years = config.discovery.min_years_required

    for job in new_jobs:
        try:
            parsed = jd_parser.parse(job.description or "")
            job.jd_parsed = parsed

            # Drop generic-title jobs that don't meet the years threshold
            if job.generic_title:
                years_req = parsed.get("years_exp")
                if years_req is not None and years_req < min_years:
                    job.status = "filtered"
                    continue

            fit = matcher.compute_fit_score(profile, parsed, job.title)
            prob = success.compute_success_probability(
                profile, job.title, job.date_posted, job.remote, job.location
            )
            ranking = config.fit_weight * fit + config.success_weight * prob

            job.fit_score = fit
            job.success_probability = prob
            job.ranking_score = round(ranking, 1)
            job.status = "evaluated"
            evaluated += 1
        except Exception as e:
            logger.error("Failed to evaluate job %s (%s): %s", job.id, job.title, e)

    session.commit()
    logger.info("Evaluated %d jobs", evaluated)
    return evaluated
