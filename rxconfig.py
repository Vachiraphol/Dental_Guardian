import os
import reflex as rx

neon_db_url = "postgresql+psycopg2://neondb_owner:npg_coV8lJhdYn1t@ep-wandering-cloud-a1nscrgz.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
database_url = os.getenv("DATABASE_URL", neon_db_url)

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

config = rx.Config(
    app_name="dental_clinic_system",
    db_url=database_url,
    backend_host="0.0.0.0",
)