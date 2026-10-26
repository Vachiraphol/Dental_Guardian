"""SRS 5.2 หน้าข้อมูลส่วนตัวของลูกค้า."""

import reflex as rx

from dental_clinic_system.components.layout import member_page
from dental_clinic_system.components.ui import card, card_title, info_row, page_header, status_badge
from dental_clinic_system.state import AppState


@rx.page(route="/profile", title="ข้อมูลส่วนตัว - Dental Guardian")
def profile() -> rx.Component:
    me = AppState.me
    return member_page(
        "profile",
        page_header(
            "ข้อมูลส่วนตัว",
            "ข้อมูลสมาชิกและข้อมูลทางการแพทย์ของคุณ",
            rx.link(rx.button(rx.icon(tag="pencil", size=14), "แก้ไขข้อมูล", color_scheme="purple", radius="full"), href="/profile/edit"),
        ),
        rx.cond(
            AppState.has_my_next,
            rx.callout(
                rx.hstack(
                    rx.text("นัดหมายถัดไป: ", rx.text.strong(AppState.my_next["date_th"] + " " + AppState.my_next["time"] + " น."),
                            " · " + AppState.my_next["service"]),
                    status_badge(AppState.my_next["status"]),
                    rx.link("ดูนัดหมาย", href="/my-appointments", size="2"),
                    align="center",
                    wrap="wrap",
                ),
                icon="calendar_clock",
                width="100%",
            ),
        ),
        rx.grid(
            card(
                card_title("ข้อมูลทั่วไป"),
                info_row("รหัสผู้ป่วย", me["id"]),
                info_row("ชื่อ-นามสกุล", me["full_name"]),
                info_row("เพศ", me["gender"]),
                info_row("วันเกิด", me["dob_th"]),
                info_row("อายุ", me["age"] + " ปี"),
                info_row("เลขบัตรประชาชน", me["national_id"]),
                info_row("วันที่สมัครสมาชิก", me["registered_th"]),
            ),
            rx.vstack(
                card(
                    card_title("ข้อมูลติดต่อ"),
                    info_row("เบอร์โทรศัพท์", me["phone"]),
                    info_row("อีเมล", me["email"]),
                    info_row("ที่อยู่", me["address"]),
                ),
                card(
                    card_title("ข้อมูลทางการแพทย์", rx.icon(tag="heart_pulse", color="var(--red-9)")),
                    info_row("โรคประจำตัว", me["disease"]),
                    info_row("ยาที่แพ้", me["allergy"]),
                    rx.text("ข้อมูลนี้จะแสดงให้ทันตแพทย์เห็นทุกครั้งที่คุณมารับบริการ", size="1", color="var(--slate-10)", margin_top="8px"),
                ),
                width="100%",
                spacing="4",
            ),
            columns={"initial": "1", "lg": "2"},
            spacing="4",
            width="100%",
        ),
    )
