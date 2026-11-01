import os
import reflex as rx
from fastapi import FastAPI
from .backend.models import QueueBooking, Appointment, TreatmentEntry
from .backend.api_queue import router as queue_router
from .backend.api import router as treatment_router
from . import pages  # noqa: F401 (registers every @rx.page)

# 1. ตั้งค่า FastAPI Instance พร้อม Swagger Docs
fastapi_app = FastAPI(
    title="Dental Guardian API",
    description="Backend API สำหรับระบบจัดการคลินิกทันตกรรม (SRS 5.3 & SRS 5.4)",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

@fastapi_app.get("/api/health")
@fastapi_app.get("/")
def read_root():
    return {
        "system": "Dental Guardian Backend",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "treatments": "/api/treatments",
            "queues": "/api/queues",
            "appointments": "/api/appointments",
        },
    }

fastapi_app.include_router(treatment_router)
fastapi_app.include_router(queue_router)

class State(rx.State):
    """The app state."""
    pass

# 2. ผูกเข้ากับ Reflex App (ตัด script observer ออก เพื่อหยุด loop)
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        accent_color="purple",
        gray_color="slate",
        radius="large",
    ),
    stylesheets=["/styles.css"],
    head_components=[
        rx.el.meta(name="color-scheme", content="light"),
        rx.el.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
        rx.el.link(rel="icon", type="image/png", href="/logo.png"),
    ],
    api_transformer=fastapi_app,
)