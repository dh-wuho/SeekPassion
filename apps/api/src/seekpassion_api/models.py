import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Float, ForeignKey, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid

from seekpassion_api.db import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class AuthProvider(enum.StrEnum):
    email = "email"
    google = "google"


class MonitoringStatus(enum.StrEnum):
    active = "active"
    paused = "paused"


class JobStatus(enum.StrEnum):
    open = "open"
    expired = "expired"


class ApplicationStatus(enum.StrEnum):
    draft = "Draft"
    preparing = "Preparing"
    waiting_review = "Waiting Review"
    applying = "Applying"
    submitted = "Submitted"
    failed = "Failed"
    rejected = "Rejected"
    accepted = "Accepted"


class BrowserSessionStatus(enum.StrEnum):
    running = "running"
    paused_review = "paused_review"
    paused_captcha = "paused_captcha"
    failed = "failed"
    completed = "completed"


class NotificationChannel(enum.StrEnum):
    in_app = "in_app"
    email = "email"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    auth_provider: Mapped[AuthProvider] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    work_authorization: Mapped[str | None] = mapped_column(String)
    sponsorship_required: Mapped[bool | None] = mapped_column()
    desired_locations: Mapped[list | None] = mapped_column(JSONType)
    salary_expectation: Mapped[str | None] = mapped_column(String)
    linkedin_url: Mapped[str | None] = mapped_column(String)
    github_url: Mapped[str | None] = mapped_column(String)
    portfolio_url: Mapped[str | None] = mapped_column(String)


class Company(Base):
    """Global, platform-curated catalog entity. Not per-user — users relate
    to companies only through Subscription."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String, nullable=False)
    career_url: Mapped[str] = mapped_column(String, nullable=False)
    ats_type: Mapped[str | None] = mapped_column(String)
    monitoring_status: Mapped[MonitoringStatus] = mapped_column(default=MonitoringStatus.active)
    last_crawl_at: Mapped[datetime | None] = mapped_column()


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_subscription_user_company"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    company: Mapped["Company"] = relationship()


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String)
    employment_type: Mapped[str | None] = mapped_column(String)
    level: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    posted_at: Mapped[datetime | None] = mapped_column()
    apply_url: Mapped[str] = mapped_column(String, nullable=False)
    dedupe_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[JobStatus] = mapped_column(default=JobStatus.open)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("job_id", "user_id", name="uq_jobmatch_job_user"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Float)
    missing_skills: Mapped[list | None] = mapped_column(JSONType)
    matching_experience_ids: Mapped[list | None] = mapped_column(JSONType)
    recommendation: Mapped[str | None] = mapped_column(String)
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ExperienceSnippet(Base):
    __tablename__ = "experience_snippets"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    technologies: Mapped[list | None] = mapped_column(JSONType)
    achievements: Mapped[list | None] = mapped_column(JSONType)
    metrics: Mapped[list | None] = mapped_column(JSONType)
    tags: Mapped[list | None] = mapped_column(JSONType)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jobs.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    included_snippet_ids: Mapped[list | None] = mapped_column(JSONType)
    file_url: Mapped[str | None] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id"), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(default=ApplicationStatus.draft)
    generated_answers: Mapped[dict | None] = mapped_column(JSONType)
    submitted_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id"), unique=True, nullable=False
    )
    status: Mapped[BrowserSessionStatus] = mapped_column(default=BrowserSessionStatus.running)
    current_page_url: Mapped[str | None] = mapped_column(String)
    action_history: Mapped[list | None] = mapped_column(JSONType)
    screenshot_urls: Mapped[list | None] = mapped_column(JSONType)
    logs_url: Mapped[str | None] = mapped_column(String)
    last_error: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class AIProviderConfig(Base):
    __tablename__ = "ai_provider_configs"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    encrypted_api_key: Mapped[bytes | None] = mapped_column(LargeBinary)
    prompt_preferences: Mapped[dict | None] = mapped_column(JSONType)
    is_active: Mapped[bool] = mapped_column(default=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(default=NotificationChannel.in_app)
    payload: Mapped[dict | None] = mapped_column(JSONType)
    read_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
