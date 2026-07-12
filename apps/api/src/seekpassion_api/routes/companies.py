import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from seekpassion_api.db import get_db
from seekpassion_api.models import Company, Subscription
from seekpassion_api.schemas import CompanyOut, SubscriptionCreate, SubscriptionOut

router = APIRouter(tags=["companies"])


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(
    user_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> list[CompanyOut]:
    companies = db.execute(select(Company)).scalars().all()

    subscribed_ids: set[uuid.UUID] = set()
    if user_id is not None:
        subscribed_ids = set(
            db.execute(
                select(Subscription.company_id).where(Subscription.user_id == user_id)
            ).scalars()
        )

    return [
        CompanyOut(
            **CompanyOut.model_validate(company).model_dump(exclude={"subscribed"}),
            subscribed=company.id in subscribed_ids,
        )
        for company in companies
    ]


@router.get("/users/{user_id}/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Subscription]:
    return db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    ).scalars().all()


@router.post(
    "/users/{user_id}/subscriptions",
    response_model=SubscriptionOut,
    status_code=status.HTTP_201_CREATED,
)
def subscribe(
    user_id: uuid.UUID, body: SubscriptionCreate, db: Session = Depends(get_db)
) -> Subscription:
    if db.get(Company, body.company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")

    existing = db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id, Subscription.company_id == body.company_id
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Already subscribed")

    subscription = Subscription(user_id=user_id, company_id=body.company_id)
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete(
    "/users/{user_id}/subscriptions/{company_id}", status_code=status.HTTP_204_NO_CONTENT
)
def unsubscribe(
    user_id: uuid.UUID, company_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    subscription = db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id, Subscription.company_id == company_id
        )
    ).scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(subscription)
    db.commit()
