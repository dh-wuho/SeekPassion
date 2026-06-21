from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from seekpassion.discovery.base import RawJob, detect_ats

logger = logging.getLogger(__name__)


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value / 1000).date()
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                return datetime.strptime(value[:19], fmt[:len(value[:19])]).date()
            except ValueError:
                continue
    return None


def _is_remote(text: str) -> bool:
    return bool(re.search(r"\bremote\b", text, re.IGNORECASE))


class GreenhouseScraper:
    def __init__(self, company_name: str, url: str, max_age_weeks: int = 4) -> None:
        self.company_name = company_name
        self.url = url
        self.max_age_weeks = max_age_weeks
        slug = self._extract_slug(url)
        self.api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

    @staticmethod
    def _extract_slug(url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        return path.split("/")[-1]

    def scrape(self) -> list[RawJob]:
        cutoff = datetime.now(timezone.utc).date() - timedelta(weeks=self.max_age_weeks)
        try:
            response = httpx.get(self.api_url, timeout=15)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Greenhouse fetch failed for %s: %s", self.company_name, e)
            return []

        jobs_data = response.json().get("jobs", [])
        results: list[RawJob] = []
        for j in jobs_data:
            posted = _parse_date(j.get("updated_at") or j.get("created_at"))
            if posted and posted < cutoff:
                continue
            loc_raw = j.get("location")
            location = loc_raw.get("name", "") if isinstance(loc_raw, dict) else ""
            content = j.get("content", "") or ""
            text = BeautifulSoup(content, "html.parser").get_text(" ") if content else ""
            results.append(
                RawJob(
                    company=self.company_name,
                    title=j.get("title", ""),
                    job_url=j.get("absolute_url", ""),
                    ats_platform="greenhouse",
                    description=text or None,
                    location=location or None,
                    remote=_is_remote(location + " " + text),
                    date_posted=posted,
                )
            )
        return results


class LeverScraper:
    def __init__(self, company_name: str, url: str, max_age_weeks: int = 4) -> None:
        self.company_name = company_name
        self.url = url
        self.max_age_weeks = max_age_weeks
        slug = urlparse(url).path.strip("/").split("/")[0]
        self.api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"

    def scrape(self) -> list[RawJob]:
        cutoff = datetime.now(timezone.utc).date() - timedelta(weeks=self.max_age_weeks)
        try:
            response = httpx.get(self.api_url, timeout=15)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Lever fetch failed for %s: %s", self.company_name, e)
            return []

        results: list[RawJob] = []
        for j in response.json():
            posted = _parse_date(j.get("createdAt"))
            if posted and posted < cutoff:
                continue
            location = j.get("categories", {}).get("location", "") or ""
            commitment = j.get("categories", {}).get("commitment", "") or ""
            description_parts = [
                BeautifulSoup(s.get("content", ""), "html.parser").get_text(" ")
                for s in j.get("descriptionBody", {}).get("descriptionSections", [])
                if s.get("content")
            ]
            text = " ".join(description_parts)
            results.append(
                RawJob(
                    company=self.company_name,
                    title=j.get("text", ""),
                    job_url=j.get("hostedUrl", ""),
                    ats_platform="lever",
                    description=text or None,
                    location=location or None,
                    remote=_is_remote(location + " " + commitment + " " + text),
                    date_posted=posted,
                )
            )
        return results


class AshbyScraper:
    def __init__(self, company_name: str, url: str, max_age_weeks: int = 4) -> None:
        self.company_name = company_name
        self.url = url
        self.max_age_weeks = max_age_weeks
        slug = urlparse(url).path.strip("/").split("/")[0]
        self.api_url = (
            f"https://api.ashbyhq.com/posting-public/apiPostingList/all"
            f"?organizationHostedJobsPageName={slug}"
        )

    def scrape(self) -> list[RawJob]:
        cutoff = datetime.now(timezone.utc).date() - timedelta(weeks=self.max_age_weeks)
        try:
            response = httpx.get(self.api_url, timeout=15)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Ashby fetch failed for %s: %s", self.company_name, e)
            return []

        data = response.json()
        postings = data.get("results", []) if isinstance(data, dict) else data
        results: list[RawJob] = []
        for j in postings:
            posted = _parse_date(j.get("publishedDate") or j.get("createdAt"))
            if posted and posted < cutoff:
                continue
            location = j.get("locationName") or j.get("location") or ""
            is_remote = j.get("isRemote", False) or _is_remote(str(location))
            results.append(
                RawJob(
                    company=self.company_name,
                    title=j.get("title", ""),
                    job_url=j.get("jobUrl", j.get("hostedUrl", "")),
                    ats_platform="ashby",
                    location=str(location) or None,
                    remote=bool(is_remote),
                    date_posted=posted,
                )
            )
        return results


def build_scraper(company_name: str, url: str, max_age_weeks: int = 4) -> Any:
    ats = detect_ats(url)
    if ats == "greenhouse":
        return GreenhouseScraper(company_name, url, max_age_weeks)
    if ats == "lever":
        return LeverScraper(company_name, url, max_age_weeks)
    if ats == "ashby":
        return AshbyScraper(company_name, url, max_age_weeks)
    logger.warning("No scraper for ATS '%s' (url=%s), skipping %s", ats, url, company_name)
    return None
