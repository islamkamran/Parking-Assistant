"""App settings, read from environment variables / the .env file.

One place for configuration: the app, Alembic and tests all import `settings` from here,
so the database URL is never duplicated.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Parking API"
    environment: str = "local"            # local | staging | production

    # mysql+pymysql://USER:PASSWORD@HOST:PORT/DB_NAME
    database_url: str = "mysql+pymysql://root:@localhost:3306/parking-assistant"
    db_echo: bool = False                 # True = print every SQL statement (debugging)

    api_key: str = "demo-key"             # the agent / Copilot Studio sends this in x-api-key
    admin_api_key: str = "admin-demo-key" # staff only (create/delete fines); never given to the agent
    webhook_secret: str = "demo-webhook-secret"   # shared with the payment gateway

    public_url: str = ""                  # e.g. https://parking-api.azurewebsites.net (used in pay links)
    payment_link_ttl_minutes: int = 15


settings = Settings()
