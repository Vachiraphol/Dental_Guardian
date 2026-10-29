import os
import reflex as rx
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from sqlmodel import select

from .backend.models import User
from .backend.api_auth import router_auth, router_patient

try:
    from .backend.api_auth import hash_password
except ImportError:
    import hashlib
    def hash_password(pwd: str) -> str:
        return hashlib.sha256(pwd.encode()).hexdigest()

from . import pages  # noqa: F401


def init_default_staff():
    """โหลดข้อมูลบัญชีระบบจาก Environment Variable โดยไม่มีข้อมูลผู้ใช้ปรากฏในโค้ด"""
    config_raw = os.getenv("DEFAULT_USERS_CONFIG", "")
    if not config_raw:
        return

    try:
        with rx.session() as session:
            # แปลงข้อความคอนฟิกเป็นรายการบัญชี
            user_entries = [entry.strip().split("|") for entry in config_raw.split(",") if entry.strip()]

            for item in user_entries:
                if len(item) != 4:
                    continue
                username, pwd_raw, full_name, role = item
                pwd_hash = hash_password(pwd_raw)

                existing = session.exec(select(User).where(User.username == username)).first()
                if not existing:
                    session.add(
                        User(
                            username=username,
                            password_hash=pwd_hash,
                            full_name=full_name,
                            role=role,
                            is_active=True,
                        )
                    )
                else:
                    existing.password_hash = pwd_hash
                    existing.role = role
                    existing.full_name = full_name
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

api_app.include_router(router_auth)
api_app.include_router(router_patient)


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