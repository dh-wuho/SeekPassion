from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String)  # linkedin | company_board
    company: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    date_posted: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    job_url: Mapped[str] = mapped_column(String, unique=True)
    ats_platform: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    jd_parsed: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    fit_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ranking_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generic_title: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="new")

    tailored_applications: Mapped[list[TailoredApplication]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    llm_suggestions: Mapped[list[LLMSuggestion]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class TailoredApplication(Base):
    __tablename__ = "tailored_applications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    selected_snippets: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    skills_reordered: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, default="draft")

    job: Mapped[Job] = relationship(back_populates="tailored_applications")


class LLMSuggestion(Base):
    __tablename__ = "llm_suggestions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    snippet_id: Mapped[str] = mapped_column(String)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"))
    original_text: Mapped[str] = mapped_column(Text)
    suggested_text: Mapped[str] = mapped_column(Text)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped[Job] = relationship(back_populates="llm_suggestions")
