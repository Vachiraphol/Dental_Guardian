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

# Route เช็คสถานะ API
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

# บังคับทั้งแอปพลิเคชันให้อยู่ในโหมด Light เสมอ พร้อมล็อกสีข้อความไม่ให้จมหายตาม Dark Mode ของเครื่อง
enforce_light_theme_css = """
/* 1. ล็อก Root Document ให้เป็น Light Scheme */
:root, html, body, .radix-themes {
    color-scheme: light !important;
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

/* 2. ล็อกสีข้อความใน Navbar / แคปซูลเมนูนำทางทั้งหมดให้เป็นสีเข้มคมชัด */
header,
header *,
nav,
nav *,
header a,
header a *,
header span,
header p,
nav a,
nav a *,
nav span,
nav p,
.radix-themes:is(.dark, [data-theme='dark']) header a,
.radix-themes:is(.dark, [data-theme='dark']) header a *,
.radix-themes:is(.dark, [data-theme='dark']) header span,
.radix-themes:is(.dark, [data-theme='dark']) header p,
.radix-themes:is(.dark, [data-theme='dark']) nav a,
.radix-themes:is(.dark, [data-theme='dark']) nav a *,
.radix-themes:is(.dark, [data-theme='dark']) nav span,
.radix-themes:is(.dark, [data-theme='dark']) nav p {
    color: #1E293B !important;
}

/* 3. ล็อกสีตัวอักษรและสีพื้นหลังของการ์ด */
.rt-Card, .rt-DialogContent {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}

/* 4. ยกเว้นปุ่มที่มีสีพื้นหลังเข้ม เช่น ปุ่มม่วง สมัครสมาชิก/เข้าสู่ระบบ ให้ตัวหนังสือเป็นสีขาวเสมอ */
.rt-Button[data-variant="solid"],
.rt-Button[data-variant="solid"] * {
    color: #FFFFFF !important;
}

/* 5. ล็อกสีตัวหนังสือของหัวข้อและข้อความทั่วไปบนพื้นขาว */
.radix-themes:is(.dark, [data-theme='dark']) h1,
.radix-themes:is(.dark, [data-theme='dark']) h2,
.radix-themes:is(.dark, [data-theme='dark']) h3,
.radix-themes:is(.dark, [data-theme='dark']) p {
    color: #1E293B !important;
}
"""

# 2. ผูกเข้ากับ Reflex App พร้อมล็อก Light Mode
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
        rx.el.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
        rx.el.link(rel="icon", type="image/png", href="/logo.png"),
        rx.el.style(enforce_light_theme_css),
    ],
    api_transformer=fastapi_app,
)