import os
import reflex as rx

# ดึงค่าจาก Environment Variable หรือใช้ค่า Default สำหรับ Local Development
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password123")  # ใส่รหัสผ่าน PostgreSQL ของคุณ
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dental_guardian_db")

DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

config = rx.Config(
    app_name="dental_clinic_system",
    db_url = "postgresql+psycopg2://postgres:password123@localhost:5432/dental_guardian_db",
    backend_host="127.0.0.1",
    backend_port=8000,
    api_url="http://localhost:8000",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                has_background=True,
                radius="large",
                accent_color="purple",
                gray_color="slate",
            )
        ),
    ],
)