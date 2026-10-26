"""SRS 5.1 หน้าล็อกอิน."""

import reflex as rx

from dental_clinic_system.components.auth_card import auth_card, password_input
from dental_clinic_system.components.layout import public_page
from dental_clinic_system.components.ui import error_callout, field
from dental_clinic_system.state import AppState


@rx.page(route="/login", title="เข้าสู่ระบบ - Dental Guardian")
def login() -> rx.Component:
    return public_page(
        auth_card(
            "log_in",
            "เข้าสู่ระบบ",
            "ยินดีต้อนรับกลับมา! กรุณากรอกข้อมูลของคุณ",
            rx.form(
                rx.vstack(
                    rx.segmented_control.root(
                        rx.segmented_control.item("ผู้ป่วย", value="patient"),
                        rx.segmented_control.item("หมอฟัน / พยาบาล", value="staff"),
                        value=AppState.login_role,
                        on_change=AppState.set_login_role,
                        width="100%",
                    ),
                    field("อีเมล", rx.input(name="email", type="email", placeholder="you@example.com", size="3", width="100%", required=True), True),
                    field("รหัสผ่าน", password_input("password"), True),
                    rx.hstack(
                        rx.spacer(),
                        rx.link("ลืมรหัสผ่าน?", href="/forgot-password", size="2"),
                        width="100%",
                    ),
                    error_callout(AppState.login_error),
                    rx.button("เข้าสู่ระบบ", type="submit", size="3", width="100%", color_scheme="purple", radius="full"),
                    rx.text("ยังไม่มีบัญชี? ", rx.link("สมัครสมาชิก", href="/register", weight="bold"), size="2", align="center", width="100%"),
                    width="100%",
                    spacing="3",
                ),
                on_submit=AppState.login,
                width="100%",
            ),
        ),
    )
