"""SRS 5.3 (พนักงาน): หน้าจัดการคำขอจองคิว — อนุมัติ / ปฏิเสธการจองที่ลูกค้าส่งมา."""

import reflex as rx

from dental_clinic_system.components.layout import staff_page
from dental_clinic_system.components.ui import card, card_title, empty_state, field, info_row, medical_flags, page_header, status_badge
from dental_clinic_system.state import AppState


def request_card(a) -> rx.Component:
    return rx.card(
        rx.flex(
            rx.vstack(
                rx.hstack(
                    rx.badge(a["id"], color_scheme="gray"),
                    status_badge(a["status"]),
                    rx.text("ส่งคำขอเมื่อ " + a["created"], size="1", color="var(--slate-9)"),
                    align="center",
                    wrap="wrap",
                ),
                rx.text(a["patient_name"], size="4", weight="bold"),
                rx.text(a["patient_id"] + " · โทร " + a["phone"], size="2", color="var(--slate-10)"),
                medical_flags(a["disease"], a["allergy"]),
                spacing="1",
                align="start",
                flex="1",
                min_width="220px",
            ),
            rx.vstack(
                info_row("วันที่", "วัน" + a["weekday"] + "ที่ " + a["date_th"]),
                info_row("เวลา", a["time"] + " น."),
                info_row("บริการ", a["service"]),
                info_row("ทันตแพทย์ที่ขอ", rx.cond(a["dentist"] != "", a["dentist"], "ไม่ระบุ")),
                rx.cond(a["note"] != "", info_row("อาการ", a["note"])),
                spacing="0",
                flex="1",
                min_width="260px",
            ),
            rx.flex(
                rx.button(rx.icon(tag="check", size=14), "อนุมัติการจอง", color_scheme="green", on_click=AppState.approve_request(a["id"])),
                rx.button(rx.icon(tag="x", size=14), "ปฏิเสธ", color_scheme="red", variant="soft", on_click=AppState.open_reject(a["id"])),
                direction="column",
                gap="8px",
                justify="center",
            ),
            gap="16px",
            wrap="wrap",
            width="100%",
            align="center",
        ),
        width="100%",
        padding="18px",
        border_left="4px solid var(--amber-9)",
    )


def reject_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("ปฏิเสธคำขอจองคิว " + AppState.reject_target),
            rx.form(
                rx.vstack(
                    field("เหตุผล (จะแจ้งให้ผู้ป่วยทราบ)",
                          rx.select(["คิวเต็มในช่วงเวลานี้", "ทันตแพทย์ไม่เข้าเวร", "บริการนี้ต้องนัดกับทันตแพทย์เฉพาะทาง", "อื่น ๆ"],
                                    name="reason", default_value="คิวเต็มในช่วงเวลานี้", width="100%")),
                    rx.hstack(
                        rx.dialog.close(rx.button("ยกเลิก", type="button", variant="soft", color_scheme="gray")),
                        rx.button("ยืนยันการปฏิเสธ", type="submit", color_scheme="red"),
                        justify="end",
                        width="100%",
                        spacing="2",
                    ),
                    spacing="4",
                    width="100%",
                    margin_top="12px",
                ),
                on_submit=AppState.reject_request,
            ),
            max_width="460px",
        ),
        open=AppState.reject_open,
        on_open_change=AppState.set_reject_open,
    )


@rx.page(route="/requests", title="จัดการคำขอจองคิว", on_load=AppState.load_schedule_data)
def requests():
    return staff_page(
        "requests",
        page_header(
            "จัดการคำขอจองคิว",
            "ตรวจสอบและยืนยันการจองคิวที่ผู้ป่วยส่งผ่านเว็บไซต์",
            rx.badge(AppState.pending_count.to_string() + " รายการรออนุมัติ", size="3", color_scheme="amber"),
        ),
        rx.cond(
            AppState.pending_requests.length() > 0,
            rx.vstack(rx.foreach(AppState.pending_requests, request_card), width="100%", spacing="3"),
            card(empty_state("ไม่มีคำขอจองคิวที่รออนุมัติ", "inbox")),
        ),
        card(
            card_title("ผลการพิจารณาล่าสุด"),
            rx.cond(
                AppState.recent_decisions.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AppState.recent_decisions,
                        lambda a: rx.hstack(
                            rx.badge(a["id"], color_scheme="gray"),
                            rx.text(a["patient_name"], weight="medium", size="2"),
                            rx.text(a["date_th"] + " " + a["time"], size="2", color="var(--slate-10)"),
                            rx.spacer(),
                            rx.cond(a["reason"] != "", rx.text(a["reason"], size="1", color="var(--slate-10)")),
                            status_badge(a["status"]),
                            width="100%",
                            align="center",
                            padding_y="8px",
                            border_bottom="1px solid var(--slate-3)",
                            wrap="wrap",
                        ),
                    ),
                    width="100%",
                    spacing="0",
                ),
                rx.text("ยังไม่มี", size="2", color="var(--slate-10)"),
            ),
        ),
        reject_dialog(),
    )
