import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from seekpassion_api.models import MonitoringStatus


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    career_url: str
    ats_type: str | None
    monitoring_status: MonitoringStatus
    last_crawl_at: datetime | None
    subscribed: bool = False


class SubscriptionCreate(BaseModel):
    company_id: uuid.UUID


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company: CompanyOut
    created_at: datetime
