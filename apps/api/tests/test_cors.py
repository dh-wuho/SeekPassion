from fastapi.testclient import TestClient


def test_companies_endpoint_allows_web_app_origin(client: TestClient) -> None:
    response = client.get("/companies", headers={"Origin": "http://localhost:3000"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
