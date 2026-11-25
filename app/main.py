import sys
from pathlib import Path

# Allow `python app/main.py`: when run as a script, Python only looks inside app/,
# so add the project root to the path before importing app.* modules.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI  # noqa: E402

from app.api import admin, checkout, fines, payments, webhooks  # noqa: E402
from app.config import settings  # noqa: E402

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Back end for an AI parking agent: fines, payment links and signed, idempotent webhooks.",
)

app.include_router(fines.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
app.include_router(checkout.router)
app.include_router(admin.router)


@app.get("/")
def mainfun():
    return {"status": "Application is Running", "environment": settings.environment}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",                        # import string: required for reload
        host="127.0.0.1",
        port=8000,
        reload=True,                           # restart automatically when code changes
        reload_dirs=[str(PROJECT_ROOT / "app")],   # watch only app/, not venv/
    )
