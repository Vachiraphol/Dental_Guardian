"""SRS 5.1 หน้ากรอกข้อมูลสมัครสมาชิก."""

import reflex as rx

from dental_clinic_system.components.auth_card import auth_card, password_input
from dental_clinic_system.components.layout import public_page
from dental_clinic_system.components.ui import error_callout, field
from dental_clinic_system.state import AppState, GENDERS


@rx.page(route="/register", title="สมัครสมาชิก - Dental Guardian")
def register() -> rx.Component:
    def section(text: str) -> rx.Component:
        return rx.text(text, weight="bold", size="3", color="var(--primary-color)", width="100%", padding_top="8px",
                       border_bottom="1px solid var(--slate-4)", padding_bottom="4px")

    grid = lambda *c: rx.grid(*c, columns={"initial": "1", "sm": "2"}, spacing="3", width="100%")
    return public_page(
        auth_card(
            "user_plus",
            "สมัครสมาชิก",
            "กรอกข้อมูลส่วนตัวเพื่อสร้างบัญชี ระบบจะสร้างรหัสผู้ป่วยให้อัตโนมัติ",
            rx.form(
                rx.vstack(
                    section("ข้อมูลส่วนตัว"),
                    grid(
                        field("ชื่อ", rx.input(name="first_name", size="3", required=True), True),
                        field("นามสกุล", rx.input(name="last_name", size="3", required=True), True),
                        field("เพศ", rx.select(GENDERS, name="gender", default_value="ไม่ระบุ", size="3", width="100%")),
                        field("วันเกิด", rx.input(name="dob", type="date", size="3", required=True), True,
                              "ใช้แสดงผังฟันตามช่วงอายุ"),
                        field("เลขบัตรประชาชน", rx.input(name="national_id", size="3", max_length=13, placeholder="13 หลัก")),
                        field("เบอร์โทรศัพท์", rx.input(name="phone", size="3", placeholder="08x-xxx-xxxx", required=True), True),
                    ),
                    field("ที่อยู่", rx.text_area(name="address", rows="2")),
                    section("ข้อมูลทางการแพทย์"),
                    grid(
                        field("โรคประจำตัว", rx.input(name="disease", size="3", placeholder="ไม่มี / เช่น เบาหวาน")),
                        field("ยาที่แพ้", rx.input(name="allergy", size="3", placeholder="ไม่มี / เช่น เพนิซิลลิน")),
                    ),
                    section("บัญชีผู้ใช้"),
                    field("อีเมล (ใช้เข้าสู่ระบบ)", rx.input(name="email", type="email", size="3", required=True), True),
                    grid(
                        field("รหัสผ่าน", password_input("password", "อย่างน้อย 8 ตัวอักษร", min_length=8), True),
                        field("ยืนยันรหัสผ่าน", password_input("confirm", "กรอกรหัสผ่านอีกครั้ง"), True),
                    ),
                    rx.hstack(
                        rx.checkbox(name="accept", required=True),
                        rx.text("ยอมรับเงื่อนไขการใช้งานและนโยบายความเป็นส่วนตัว", size="2"),
                        align="center",
                        width="100%",
                    ),
                    error_callout(AppState.register_error),
                    rx.button("สร้างบัญชีผู้ใช้", type="submit", size="3", width="100%", color_scheme="purple", radius="full"),
                    rx.text("มีบัญชีอยู่แล้ว? ", rx.link("เข้าสู่ระบบ", href="/login", weight="bold"), size="2", align="center", width="100%"),
                    width="100%",
                    spacing="3",
                ),
                on_submit=AppState.register,
                width="100%",
            ),
            max_width="640px",
        ),
    )
