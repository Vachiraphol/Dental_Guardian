"""SRS 5.2 หน้าแก้ไขข้อมูลส่วนตัว."""

import reflex as rx

from dental_clinic_system.components.layout import member_page
from dental_clinic_system.components.ui import card, card_title, field, page_header
from dental_clinic_system.state import AppState, GENDERS


@rx.page(route="/profile/edit", title="แก้ไขข้อมูลส่วนตัว - Dental Guardian")
def edit_profile() -> rx.Component:
    me = AppState.me
    grid = lambda *c: rx.grid(*c, columns={"initial": "1", "sm": "2"}, spacing="3", width="100%")
    return member_page(
        "edit",
        page_header("แก้ไขข้อมูลส่วนตัว", "ปรับปรุงข้อมูลให้เป็นปัจจุบันเพื่อการรักษาที่ปลอดภัย"),
        card(
            rx.form(
                rx.vstack(
                    card_title("ข้อมูลทั่วไป"),
                    grid(
                        field("ชื่อ", rx.input(name="first_name", default_value=me["first_name"], size="3", required=True), True),
                        field("นามสกุล", rx.input(name="last_name", default_value=me["last_name"], size="3", required=True), True),
                        field("เพศ", rx.select(GENDERS, name="gender", default_value=me["gender"], size="3", width="100%")),
                        field("วันเกิด", rx.input(name="dob", type="date", default_value=me["dob"], size="3")),
                        field("เลขบัตรประชาชน", rx.input(name="national_id", default_value=me["national_id"], size="3", max_length=13)),
                    ),
                    card_title("ข้อมูลติดต่อ"),
                    grid(
                        field("เบอร์โทรศัพท์", rx.input(name="phone", default_value=me["phone"], size="3", required=True), True),
                        field("อีเมล", rx.input(name="email", type="email", default_value=me["email"], size="3", required=True), True),
                    ),
                    field("ที่อยู่", rx.text_area(name="address", default_value=me["address"], rows="2")),
                    card_title("ข้อมูลทางการแพทย์"),
                    grid(
                        field("โรคประจำตัว", rx.input(name="disease", default_value=me["disease"], size="3", placeholder="ไม่มี")),
                        field("ยาที่แพ้", rx.input(name="allergy", default_value=me["allergy"], size="3", placeholder="ไม่มี")),
                    ),
                    rx.hstack(
                        rx.link(rx.button("ยกเลิก", type="button", variant="soft", color_scheme="gray"), href="/profile"),
                        rx.button(rx.icon(tag="save", size=14), "บันทึกข้อมูล", type="submit", color_scheme="purple"),
                        justify="end",
                        width="100%",
                        spacing="2",
                    ),
                    width="100%",
                    spacing="3",
                ),
                on_submit=AppState.save_profile,
                width="100%",
                # remount the form when the logged-in patient changes so default values refresh
                key=me["id"],
            ),
        ),
    )
