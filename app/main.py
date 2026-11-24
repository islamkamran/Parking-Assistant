from fastapi import FastAPI

from app.api import checkout, fines, payments, webhooks
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Back end for an AI parking agent: fines, payment links and signed, idempotent webhooks.",
)

app.include_router(fines.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
app.include_router(checkout.router)

@app.get("/")
def mainfun():
    return {"status": "Application is Running", "environment": settings.environment}

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "environment": settings.environment}
