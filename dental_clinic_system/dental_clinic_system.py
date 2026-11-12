import os
import reflex as rx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .backend.database import init_db
from .backend.models import QueueBooking, Appointment, TreatmentEntry, User, PatientProfile
from .backend.api_auth import router as auth_router
from .backend.api_queue import router as queue_router
from .backend.api import router as treatment_router
from . import pages  # noqa: F401

# 1. ตั้งค่า FastAPI App
fastapi_app = FastAPI(
    title="Dental Guardian API",
    description="Backend API ระบบจัดการคลินิกทันตกรรม (SRS 5.1 - SRS 5.4)",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# 2. ผูก CORS Middleware รองรับการเรียกจาก Vercel และ Localhost
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dental-guardian-web.vercel.app",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. รันการตรวจสอบและสร้างตารางบน Database (Neon)
@fastapi_app.on_event("startup")
def on_startup():
    init_db()

# Route Health Check
@fastapi_app.get("/api/health")
@fastapi_app.get("/")
def read_root():
    return {
        "system": "Dental Guardian Backend",
        "status": "online",
        "version": "1.2.0",
        "docs_url": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "treatments": "/api/treatments",
            "queues": "/api/queues",
            "appointments": "/api/appointments",
        },
    }

# 4. รวม Routers ทั้งหมด
fastapi_app.include_router(auth_router)
fastapi_app.include_router(treatment_router)
fastapi_app.include_router(queue_router)

class State(rx.State):
    """The app state."""
    pass

# 5. ผูกเข้ากับ Reflex App
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
        rx.el.meta(name="color-scheme", content="only light"),
        rx.el.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
        rx.el.link(rel="icon", type="image/png", href="/logo.png"),
    ],
    api_transformer=fastapi_app,
)