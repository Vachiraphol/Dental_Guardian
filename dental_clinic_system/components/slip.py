"""Booking slip / appointment card (ใบจองคิว / ใบนัด) — shown to the clinic front desk."""

import reflex as rx

from dental_clinic_system.components.brand import logo
from dental_clinic_system.components.ui import info_row, status_badge
from dental_clinic_system.state import AppState


def slip_card(a) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                logo("40px"),
                rx.vstack(
                    rx.text("Dental Guardian", weight="bold", size="3"),
                    rx.text(rx.cond(a["kind"] == "นัดครั้งถัดไป", "ใบนัดครั้งถัดไป", "ใบจองคิว"), size="1", color="var(--slate-10)"),
                    spacing="0",
                ),
                align="center",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text("เลขที่", size="1", color="var(--slate-10)"),
                rx.text(a["id"], weight="bold", size="4", class_name="gradient-text"),
                spacing="0",
                align="end",
            ),
            width="100%",
            align="center",
            padding_bottom="12px",
            border_bottom="2px dashed var(--slate-5)",
        ),
        rx.center(
            rx.vstack(
                rx.text("วัน" + a["weekday"] + "ที่ " + a["date_th"], size="4", weight="bold"),
                rx.text("เวลา " + a["time"] + " น.", size="7", weight="bold", color="var(--primary-color)"),
                align="center",
                spacing="0",
            ),
            padding_y="16px",
        ),
        info_row("ชื่อผู้ป่วย", a["patient_name"]),
        info_row("เบอร์โทรศัพท์", a["phone"]),
        info_row("บริการ", a["service"]),
        info_row("ทันตแพทย์", rx.cond(a["dentist"] != "", a["dentist"], "คลินิกจัดให้")),
        rx.cond(a["purpose"] != "", info_row("นัดเพื่อ", a["purpose"])),
        info_row("โรคประจำตัว", a["disease"]),
        info_row("ยาที่แพ้", a["allergy"]),
        rx.hstack(rx.text("สถานะ", size="2", color="var(--slate-10)", min_width="140px"), status_badge(a["status"]),
                  padding_y="8px", width="100%"),
        rx.text("กรุณาแสดงใบนี้ที่เคาน์เตอร์ และมาก่อนเวลานัด 15 นาที", size="1", color="var(--slate-10)",
                align="center", width="100%", margin_top="12px"),
        padding="20px",
        border="1px solid var(--slate-5)",
        border_radius="16px",
        background_color="white",
        width="100%",
        id="slip",
    )


def slip_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("ใบนัด / ใบจองคิว", class_name="no-print"),
            slip_card(AppState.slip),
            rx.hstack(
                rx.button(rx.icon(tag="calendar_plus", size=14), "เพิ่มลงปฏิทิน (.ics)", variant="soft",
                          on_click=AppState.download_ics(AppState.slip["id"])),
                rx.button(rx.icon(tag="printer", size=14), "พิมพ์", variant="soft", on_click=rx.call_script("window.print()")),
                rx.dialog.close(rx.button("ปิด", color_scheme="gray", variant="soft")),
                justify="end",
                margin_top="16px",
                spacing="2",
                wrap="wrap",
                class_name="no-print",
            ),
            max_width="480px",
        ),
        open=AppState.slip_open,
        on_open_change=AppState.set_slip_open,
    )
