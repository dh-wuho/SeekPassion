from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from ruamel.yaml import YAML


class CompanyConfig(BaseModel):
    name: str
    url: str


class DiscoveryConfig(BaseModel):
    max_job_age_weeks: int = 4
    domains: list[str] = Field(default_factory=lambda: ["engineering"])
    title_exclude: list[str] = Field(default_factory=list)
    min_years_required: int = 4


class ResumeConfig(BaseModel):
    static_file: str
    pool_file: str


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: Optional[str] = None
    api_key: str = ""
    base_url: Optional[str] = None


class Config(BaseModel):
    companies: list[CompanyConfig] = Field(default_factory=list)
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    resume: ResumeConfig
    fit_weight: float = 0.6
    success_weight: float = 0.4
    min_fit_score: float = 40.0
    daily_application_limit: int = 50
    snippet_select_n: int = 5
    notification_email: str = ""
    llm: Optional[LLMConfig] = None


def load_config(path: Path | str = "config.yaml") -> Config:
    yaml = YAML()
    with open(path) as f:
        data = yaml.load(f)
    return Config.model_validate(data)
