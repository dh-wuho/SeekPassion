from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from seekpassion_api.routes import companies

app = FastAPI(title="Seek Passion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
