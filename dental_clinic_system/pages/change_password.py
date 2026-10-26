"""SRS 5.2 หน้าเปลี่ยนรหัสผ่าน."""

import reflex as rx

from dental_clinic_system.components.layout import member_page
from dental_clinic_system.components.ui import card, error_callout, field, page_header
from dental_clinic_system.state import AppState


@rx.page(route="/profile/password", title="เปลี่ยนรหัสผ่าน - Dental Guardian")
def change_password() -> rx.Component:
    def pw(name: str, placeholder: str = "••••••••"):
        return rx.input(name=name, type="password", placeholder=placeholder, size="3", width="100%", required=True)

    return member_page(
        "password",
        page_header("เปลี่ยนรหัสผ่าน", "เพื่อความปลอดภัย ควรเปลี่ยนรหัสผ่านเป็นประจำ"),
        card(
            rx.form(
                rx.vstack(
                    field("รหัสผ่านปัจจุบัน", pw("current"), True),
                    field("รหัสผ่านใหม่", pw("new", "อย่างน้อย 8 ตัวอักษร"), True,
                          "ควรมีตัวอักษรภาษาอังกฤษ ตัวเลข และไม่ซ้ำกับรหัสเดิม"),
                    field("ยืนยันรหัสผ่านใหม่", pw("confirm"), True),
                    error_callout(AppState.password_error),
                    rx.hstack(
                        rx.link("ลืมรหัสผ่านปัจจุบัน?", href="/forgot-password", size="2"),
                        rx.spacer(),
                        rx.button(rx.icon(tag="key_round", size=14), "เปลี่ยนรหัสผ่าน", type="submit", color_scheme="purple"),
                        width="100%",
                        align="center",
                    ),
                    width="100%",
                    spacing="3",
                ),
                on_submit=AppState.change_password,
                reset_on_submit=True,
                width="100%",
            ),
            max_width="520px",
        ),
    )
