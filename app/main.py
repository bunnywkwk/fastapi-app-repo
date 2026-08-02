from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from typing import List
from app.config import settings
from app.database import check_db_connection

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None


# In-memory fallback / demo store
items_db: List[Item] = []


@app.get("/")
def read_root():
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "status": "healthy v5.0"
    }


@app.get("/health/liveness", status_code=status.HTTP_200_OK)
def liveness_probe():
    return {"status": "alive"}


@app.get("/health/readiness")
def readiness_probe(response: Response):
    db_healthy = check_db_connection()
    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "database": "disconnected"}
    return {"status": "ready", "database": "connected"}


@app.get("/items", response_model=List[Item])
def get_items():
    return items_db


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    items_db.append(item)
    return item
