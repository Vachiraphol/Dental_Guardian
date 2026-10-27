"""SRS 5.3 (ลูกค้า) หน้าตารางเวลาและสร้างการจองคิว."""

import reflex as rx

from dental_clinic_system.components.booking_steps import step_bar
from dental_clinic_system.components.layout import public_page
from dental_clinic_system.components.ui import card, card_title, empty_state, field
from dental_clinic_system.state import AppState, SERVICES


def day_button(d) -> rx.Component:
    selected = AppState.booking_date == d["iso"]
    closed = d["closed"] == "1"
    return rx.vstack(
        rx.text(d["weekday"], size="1", color=rx.cond(selected, "white", "var(--slate-10)")),
        rx.text(d["day"], size="5", weight="bold", color=rx.cond(selected, "white", "var(--slate-12)")),
        rx.text(d["month"], size="1", color=rx.cond(selected, "white", "var(--slate-10)")),
        rx.text(rx.cond(closed, "ปิด", rx.cond(d["free"] == "0", "เต็ม", rx.cond(d["free"] != "", "ว่าง " + d["free"], ""))), size="1",
                color=rx.cond(selected, "white", rx.cond(closed | (d["free"] == "0"), "var(--red-10)", "var(--green-11)"))),
        align="center",
        spacing="0",
        padding_y="10px",
        border_radius="14px",
        border=rx.cond(selected, "2px solid var(--purple-9)", "1px solid var(--slate-5)"),
        background_color=rx.cond(selected, "var(--purple-9)", rx.cond(closed, "var(--slate-3)", "white")),
        cursor=rx.cond(closed, "not-allowed", "pointer"),
        opacity=rx.cond(closed, "0.6", "1"),
        on_click=rx.cond(closed, rx.noop(), AppState.pick_date(d["iso"])),
        width="100%",
        _hover={"border_color": "var(--purple-8)"},
    )


def slot_button(s) -> rx.Component:
    selected = AppState.booking_time == s["time"]
    available = s["available"] == "1"
    return rx.button(
        rx.vstack(
            rx.text(s["time"], weight="bold"),
            rx.text(rx.cond(available, "ว่าง " + s["left"] + " คิว", "เต็ม"), size="1"),
            spacing="0",
            align="center",
        ),
        variant=rx.cond(selected, "solid", "outline"),
        color_scheme=rx.cond(available, "purple", "gray"),
        disabled=~available,
        on_click=AppState.pick_time(s["time"]),
        height="auto",
        padding_y="8px",
        width="100%",
    )


@rx.page(route="/booking", title="จองคิว - Dental Guardian")
def booking() -> rx.Component:
    me = AppState.me
    return public_page(
        # TODO(backend): show login_required(...) instead when the visitor is not a logged-in patient
        rx.vstack(
            step_bar(1),
            rx.flex(
                rx.vstack(
                    card(
                        card_title("1. เลือกบริการและทันตแพทย์"),
                        rx.grid(
                            field("บริการทางทันตกรรม", rx.select(SERVICES, value=AppState.booking_service,
                                                                on_change=AppState.set_booking_service, size="3", width="100%")),
                            field("ทันตแพทย์", rx.select(AppState.booking_dentist_options, value=AppState.booking_dentist,
                                                        on_change=AppState.set_booking_dentist, size="3", width="100%")),
                            columns={"initial": "1", "sm": "2"},
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    card(
                        card_title("2. เลือกวัน (14 วันข้างหน้า)",
                                   rx.text(AppState.booking_date_th, size="2", color="var(--primary-color)", weight="medium")),
                        rx.grid(rx.foreach(AppState.booking_days, day_button),
                                columns={"initial": "4", "sm": "7"}, spacing="2", width="100%"),
                    ),
                    card(
                        card_title("3. เลือกช่วงเวลา"),
                        rx.cond(
                            AppState.booking_slots.length() > 0,
                            rx.grid(rx.foreach(AppState.booking_slots, slot_button),
                                    columns={"initial": "3", "sm": "5", "lg": "6"}, spacing="2", width="100%"),
                            empty_state("คลินิกปิดหรือทันตแพทย์ไม่เข้าเวรในวันนี้ กรุณาเลือกวันอื่น", "calendar_x"),
                        ),
                    ),
                    flex="2",
                    width="100%",
                    spacing="4",
                    min_width="0",
                ),
                card(
                    card_title("4. รายละเอียดการจอง"),
                    rx.form(
                        rx.vstack(
                            rx.box(
                                rx.text("วันและเวลาที่เลือก", size="1", color="var(--slate-10)"),
                                rx.text(AppState.booking_date_th, weight="bold"),
                                rx.text(rx.cond(AppState.booking_time != "", "เวลา " + AppState.booking_time + " น.", "ยังไม่ได้เลือกเวลา"),
                                        weight="bold", color=rx.cond(AppState.booking_time != "", "var(--primary-color)", "var(--red-10)")),
                                padding="12px",
                                border_radius="10px",
                                background_color="var(--primary-light)",
                                width="100%",
                            ),
                            field("ชื่อ-นามสกุล", rx.input(name="name", default_value=me["full_name"], size="3", required=True), True),
                            field("เบอร์โทรศัพท์", rx.input(name="phone", default_value=me["phone"], size="3", required=True), True),
                            field("โรคประจำตัว", rx.input(name="disease", default_value=me["disease"], size="3", placeholder="ไม่มี")),
                            field("ยาที่แพ้", rx.input(name="allergy", default_value=me["allergy"], size="3", placeholder="ไม่มี")),
                            field("อาการ / หมายเหตุ", rx.text_area(name="note", rows="3", placeholder="เช่น ปวดฟันกรามล่างขวา")),
                            rx.button("ถัดไป: สรุปการจอง", rx.icon(tag="arrow_right", size=16), type="submit", size="3",
                                      width="100%", color_scheme="purple", radius="full", disabled=AppState.booking_time == ""),
                            width="100%",
                            spacing="3",
                        ),
                        on_submit=AppState.submit_booking_details,
                        width="100%",
                        key=me["id"],
                    ),
                    flex="1",
                    position=["static", "static", "sticky"],
                    top="16px",
                ),
                direction={"initial": "column", "lg": "row"},
                gap="16px",
                width="100%",
                align="start",
            ),
            width="100%",
            spacing="5",
        ),
        hero_title="จองคิวออนไลน์",
        hero_text="ดูตารางวัน/เวลาที่คลินิกว่าง แล้วจองคิวได้ทันทีโดยไม่ต้องไปรอหน้าคลินิก",
    )
