"""SRS 5.1 หน้าลืมรหัสผ่าน."""

import reflex as rx

from dental_clinic_system.components.auth_card import auth_card, password_input
from dental_clinic_system.components.layout import public_page
from dental_clinic_system.components.ui import error_callout, field
from dental_clinic_system.state import AppState


def _steps() -> rx.Component:
    def dot(n: int, text: str):
        return rx.vstack(
            rx.center(
                rx.text(str(n), size="1", weight="bold", color=rx.cond(AppState.reset_step >= n, "white", "var(--slate-10)")),
                width="28px", height="28px", border_radius="50%",
                background_color=rx.cond(AppState.reset_step >= n, "var(--primary-color)", "var(--slate-4)"),
            ),
            rx.text(text, size="1", color="var(--slate-10)"),
            align="center",
            spacing="1",
        )

    return rx.hstack(dot(1, "ยืนยันอีเมล"), dot(2, "ตั้งรหัสใหม่"), dot(3, "เสร็จสิ้น"), justify="center", spacing="6", width="100%")


@rx.page(route="/forgot-password", title="ลืมรหัสผ่าน - Dental Guardian")
def forgot_password() -> rx.Component:
    return public_page(
        auth_card(
            "key_round",
            "ลืมรหัสผ่าน",
            "รีเซ็ตรหัสผ่านโดยยืนยันตัวตนผ่านอีเมล",
            _steps(),
            rx.match(
                AppState.reset_step,
                (1, rx.form(
                    rx.vstack(
                        field("อีเมลที่ใช้สมัครสมาชิก", rx.input(name="email", type="email", size="3", width="100%", required=True), True),
                        error_callout(AppState.reset_error),
                        rx.button("ส่งรหัสยืนยันไปที่อีเมล", type="submit", size="3", width="100%", color_scheme="purple", radius="full"),
                        width="100%",
                        spacing="3",
                    ),
                    on_submit=AppState.request_reset,
                    width="100%",
                )),
                (2, rx.form(
                    rx.vstack(
                        rx.callout(
                            rx.text("ส่งรหัสยืนยัน 6 หลักไปที่ ", rx.text.strong(AppState.reset_email), " แล้ว"),
                            icon="mail_check", size="1", width="100%",
                        ),
                        field("รหัสยืนยัน (OTP)", rx.input(name="otp", size="3", max_length=6, placeholder="______", width="100%", required=True), True),
                        field("รหัสผ่านใหม่", password_input("password", "อย่างน้อย 8 ตัวอักษร"), True),
                        field("ยืนยันรหัสผ่านใหม่", password_input("confirm"), True),
                        error_callout(AppState.reset_error),
                        rx.button("ตั้งรหัสผ่านใหม่", type="submit", size="3", width="100%", color_scheme="purple", radius="full"),
                        rx.button("เปลี่ยนอีเมล", type="button", variant="ghost", width="100%", on_click=AppState.restart_reset),
                        width="100%",
                        spacing="3",
                    ),
                    on_submit=AppState.confirm_reset,
                    width="100%",
                )),
                rx.vstack(
                    rx.icon(tag="circle_check", size=48, color="var(--green-9)"),
                    rx.text("ตั้งรหัสผ่านใหม่เรียบร้อยแล้ว", weight="bold"),
                    rx.link(rx.button("กลับไปเข้าสู่ระบบ", size="3", color_scheme="purple", radius="full",
                                      on_click=AppState.restart_reset), href="/login"),
                    align="center",
                    spacing="3",
                ),
            ),
            rx.link("กลับไปหน้าเข้าสู่ระบบ", href="/login", size="2"),
        ),
    )
