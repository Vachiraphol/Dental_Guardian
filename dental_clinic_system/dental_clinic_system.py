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

# บังคับสีตัวหนังสือให้เป็นสีเข้ม แม้เครื่องผู้ใช้จะเปิด Dark Mode อยู่ก็ตาม
dark_mode_fix_css = """
/* บังคับลิงก์และข้อความใน Navbar ด้านบนทั้งหมดให้เป็นสีเข้ม */
header nav a, 
header nav span, 
header nav p, 
header a, 
nav a, 
nav span,
.radix-themes:is(.dark, [data-theme='dark']) header a,
.radix-themes:is(.dark, [data-theme='dark']) nav a {
    color: #111827 !important;
}

/* บังคับหัวข้อบริการทางทันตกรรมและส่วนเนื้อหาบนการ์ดขาว */
.radix-themes:is(.dark, [data-theme='dark']) h2,
.radix-themes:is(.dark, [data-theme='dark']) .rt-Heading {
    color: #111827 !important;
}

/* ยกเว้นปุ่มที่มีพื้นหลังสีม่วง เช่น สมัครสมาชิก หรือปุ่มนัดหมาย ให้ตัวหนังสือเป็นสีขาว */
header button, 
nav button, 
.rt-Button[data-variant="solid"] {
    color: #ffffff !important;
}
"""

# 2. ผูกเข้ากับ Reflex App พร้อมบังคับ appearance="light"
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
    ),
    stylesheets=["/styles.css"],
    head_components=[
        rx.el.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
        rx.el.link(rel="icon", type="image/png", href="/logo.png"),
        rx.el.style(dark_mode_fix_css),
    ],
    api_transformer=fastapi_app,
)