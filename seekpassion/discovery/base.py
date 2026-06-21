from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional, Protocol


@dataclass
class RawJob:
    company: str
    title: str
    job_url: str
    ats_platform: str
    source: str = "company_board"
    description: Optional[str] = None
    location: Optional[str] = None
    remote: bool = False
    date_posted: Optional[date] = None


class Scraper(Protocol):
    def scrape(self) -> list[RawJob]: ...


def detect_ats(url: str) -> str:
    url = url.lower()
    if "greenhouse.io" in url:
        return "greenhouse"
    if "lever.co" in url:
        return "lever"
    if "myworkdayjobs.com" in url or "workday.com" in url:
        return "workday"
    if "icims.com" in url:
        return "icims"
    if "taleo.net" in url:
        return "taleo"
    if "smartrecruiters.com" in url:
        return "smartrecruiters"
    if "ashbyhq.com" in url:
        return "ashby"
    return "unknown"
