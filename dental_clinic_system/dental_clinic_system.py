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

# Route หน้าแรก ป้องกัน Not Found
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

# รวม Router ทั้งประวัติการรักษา (5.4) และคิว/การนัดหมาย (5.3)
fastapi_app.include_router(treatment_router)
fastapi_app.include_router(queue_router)

class State(rx.State):
    """The app state."""
    pass

# 2. ผูกเข้ากับ Reflex App ผ่าน api_transformer
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
        rx.el.link(rel="icon", type="image/png", href="/logo.png"),
    ],
    api_transformer=fastapi_app,  # เชื่อมต่อ FastAPI กับ Reflex Backend
)