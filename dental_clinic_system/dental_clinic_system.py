import reflex as rx
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from sqlmodel import select

from .backend.models import User
from .backend.api_auth import router_auth, router_patient
from . import pages  # noqa: F401


def init_default_staff():
    """สร้างบัญชีทันตแพทย์และผู้ช่วย รหัสผ่านจำง่ายสำหรับการทดสอบ"""
    try:
        with rx.session() as session:
            default_users = [
                # ทันตแพทย์ 4 ท่าน
                ("dentist@dental.com", "dentist1111", "ทพ. สมศักดิ์ รักฟัน", "dentist"),
                ("dentist2@dental.com", "dentist2222", "ทพญ. พิมพา ยิ้มสวย", "dentist"),
                ("dentist3@dental.com", "dentist3333", "ทพ. ชาญชัย สุขภาพดี", "dentist"),
                ("dentist4@dental.com", "dentist4444", "ทพญ. ณิชา อารมณ์ดี", "dentist"),
                # ผู้ช่วยทันตแพทย์ / เจ้าหน้าที่คิว
                ("staff@dental.com", "staff1234", "น.ส. ใจดี ดูแลคิว (ผู้ช่วยทันตแพทย์)", "staff"),
            ]
            for email, pwd, name, role in default_users:
                existing = session.exec(select(User).where(User.username == email)).first()
                if not existing:
                    session.add(
                        User(
                            username=email,
                            password_hash=pwd,
                            full_name=name,
                            role=role,
                            is_active=True,
                        )
                    )
                else:
                    existing.password_hash = pwd
                    existing.role = role
                    existing.full_name = name
                    session.add(existing)

            session.commit()
    except Exception:
        pass

init_default_staff()

class State(rx.State):
    """The app state."""
    pass


# 1. ให้บริการเฉพาะ REST API ของ SRS 5.1 และ SRS 5.2
api_app = FastAPI(
    title="Dental Guardian REST API (SRS 5.1 & 5.2)",
    description="ระบบเวชระเบียนผู้ป่วย (5.1) และการยืนยันตัวตน/สมาชิก (5.2)",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# ผูกเฉพาะโมดูลที่รับผิดชอบใน branch นี้
api_app.include_router(router_auth)       # SRS 5.2
api_app.include_router(router_patient)    # SRS 5.1


# 2. Handler สำหรับหน้า root (/) ของ Backend พอร์ต 8000
async def root_status(request):
    return JSONResponse({
        "system": "Dental Guardian Backend API (SRS 5.1 & 5.2)",
        "status": "online",
        "web_ui": "http://localhost:3000",
        "api_docs": "http://127.0.0.1:8000/api/docs",
    })


# 3. นำ api_app ไป Mount เข้ากับ Starlette routes
def setup_api(asgi_app):
    asgi_app.routes.append(Route("/", endpoint=root_status))
    asgi_app.routes.append(Mount("/api", app=api_app))
    return asgi_app


# 4. สร้าง Reflex App
app = rx.App(
    stylesheets=["/styles.css"],
    head_components=[
        rx.el.link(
            rel="stylesheet",
            href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        ),
        rx.el.link(rel="icon", type="image/png", href="/favicon.png"),
    ],
    api_transformer=setup_api,
)