import reflex as rx
from .backend.models import TreatmentEntry
from fastapi import FastAPI
from .backend.api import router
from . import pages  # noqa: F401  (registers every @rx.page)

# 1. สร้าง FastAPI Instance พร้อมเปิดหน้า Swagger Docs
fastapi_app = FastAPI(
    title="Dental Guardian API (SRS 5.4)",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# เพิ่ม Route สำหรับหน้าแรกของ Backend (/) เพื่อไม่ให้ขึ้น Not Found
@fastapi_app.get("/")
def read_root():
    return {
        "system": "Dental Guardian Backend",
        "status": "online",
        "api_docs": "http://127.0.0.1:8000/docs",
        "treatments_api": "http://127.0.0.1:8000/api/treatments",
    }

fastapi_app.include_router(router)

class State(rx.State):
    """The app state."""
    pass

# 2. ส่ง fastapi_app เข้าไปใน api_transformer
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="large",
        accent_color="purple",
        font_family="Kanit",
    ),
    stylesheets=["/styles.css"],
    head_components=[
        rx.el.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
        rx.el.link(rel="icon", type="image/png", href="/favicon.png"),
    ],
    api_transformer=fastapi_app,  # <--- จุดสำคัญที่ทำให้ API ติดเข้ากับ Backend
)