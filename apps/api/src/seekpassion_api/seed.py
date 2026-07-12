"""Seed a demo user and a handful of catalog companies for local dev.

No auth system exists yet (out of scope for this vertical slice), so a
fixed demo user id is used across the API and frontend until real auth
lands. Run with: uv run --package seekpassion-api python -m seekpassion_api.seed
"""

import uuid

from seekpassion_api.db import SessionLocal
from seekpassion_api.models import AuthProvider, Company, User

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

DEMO_COMPANIES = [
    ("Anthropic", "https://boards.greenhouse.io/anthropic", "greenhouse"),
    ("Stripe", "https://jobs.lever.co/stripe", "lever"),
    ("Figma", "https://boards.greenhouse.io/figma", "greenhouse"),
    ("Notion", "https://jobs.lever.co/notion", "lever"),
    ("Vercel", "https://boards.greenhouse.io/vercel", "greenhouse"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.get(User, DEMO_USER_ID) is None:
            db.add(
                User(
                    id=DEMO_USER_ID,
                    email="demo@seekpassion.dev",
                    auth_provider=AuthProvider.email,
                )
            )

        existing_names = {c.name for c in db.query(Company).all()}
        for name, career_url, ats_type in DEMO_COMPANIES:
            if name not in existing_names:
                db.add(Company(name=name, career_url=career_url, ats_type=ats_type))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
