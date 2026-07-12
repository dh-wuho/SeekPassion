import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from seekpassion_api.models import Company, User


def test_list_companies_returns_catalog(client: TestClient, demo_company: Company) -> None:
    response = client.get("/companies")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Anthropic"
    assert body[0]["subscribed"] is False


def test_list_companies_marks_subscribed_for_given_user(
    client: TestClient, db_session: Session, demo_user: User, demo_company: Company
) -> None:
    client.post(f"/users/{demo_user.id}/subscriptions", json={"company_id": str(demo_company.id)})

    response = client.get("/companies", params={"user_id": str(demo_user.id)})

    assert response.status_code == 200
    assert response.json()[0]["subscribed"] is True


def test_subscribe_creates_subscription(
    client: TestClient, demo_user: User, demo_company: Company
) -> None:
    response = client.post(
        f"/users/{demo_user.id}/subscriptions", json={"company_id": str(demo_company.id)}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["company"]["id"] == str(demo_company.id)


def test_subscribe_to_unknown_company_returns_404(client: TestClient, demo_user: User) -> None:
    response = client.post(
        f"/users/{demo_user.id}/subscriptions", json={"company_id": str(uuid.uuid4())}
    )

    assert response.status_code == 404


def test_subscribe_twice_returns_409(
    client: TestClient, demo_user: User, demo_company: Company
) -> None:
    payload = {"company_id": str(demo_company.id)}
    first = client.post(f"/users/{demo_user.id}/subscriptions", json=payload)
    second = client.post(f"/users/{demo_user.id}/subscriptions", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_list_subscriptions_returns_only_this_users_companies(
    client: TestClient, demo_user: User, demo_company: Company
) -> None:
    client.post(f"/users/{demo_user.id}/subscriptions", json={"company_id": str(demo_company.id)})
    other_user_id = uuid.uuid4()

    mine = client.get(f"/users/{demo_user.id}/subscriptions")
    others = client.get(f"/users/{other_user_id}/subscriptions")

    assert len(mine.json()) == 1
    assert mine.json()[0]["company"]["name"] == "Anthropic"
    assert others.json() == []


def test_unsubscribe_removes_subscription(
    client: TestClient, demo_user: User, demo_company: Company
) -> None:
    client.post(f"/users/{demo_user.id}/subscriptions", json={"company_id": str(demo_company.id)})

    response = client.delete(f"/users/{demo_user.id}/subscriptions/{demo_company.id}")
    remaining = client.get(f"/users/{demo_user.id}/subscriptions")

    assert response.status_code == 204
    assert remaining.json() == []


def test_unsubscribe_when_not_subscribed_returns_404(
    client: TestClient, demo_user: User, demo_company: Company
) -> None:
    response = client.delete(f"/users/{demo_user.id}/subscriptions/{demo_company.id}")

    assert response.status_code == 404


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
