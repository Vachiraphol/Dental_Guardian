"""SRS 5.3 (พนักงาน): หน้าแดชบอร์ดผู้ป่วยรายวัน."""

import reflex as rx

from dental_clinic_system.components.layout import staff_page
from dental_clinic_system.components.ui import card, card_title, empty_state, medical_flags, page_header, status_badge, table_wrap
from dental_clinic_system.state import AppState


def stat(title: str, value, icon: str, color: str) -> rx.Component:
    return card(
        rx.hstack(
            rx.vstack(
                rx.text(title, size="2", color="var(--slate-11)"),
                rx.text(value, size="7", weight="bold"),
                spacing="0",
            ),
            rx.spacer(),
            rx.center(
                rx.icon(tag=icon, size=22, color=f"var(--{color}-9)"),
                background=f"var(--{color}-3)",
                padding="10px",
                border_radius="12px",
            ),
            width="100%",
            align="center",
        ),
        padding="18px",
    )


def row_actions(a) -> rx.Component:
    return rx.hstack(
        rx.cond(
            a["status"] == "รออนุมัติ",
            rx.link(rx.button("พิจารณา", size="1", color_scheme="amber"), href="/requests"),
            rx.cond(
                (a["status"] == "ยืนยันแล้ว") | (a["status"] == "เลื่อนนัด"),
                rx.button(
                    rx.icon(tag="user_check", size=14),
                    "มาตามนัด",
                    size="1",
                    color_scheme="green",
                    on_click=AppState.mark_arrived(a["id"]),
                ),
            ),
        ),
        rx.cond(
            a["status"] == "มาตามนัด",
            rx.button(
                rx.icon(tag="clipboard_pen", size=14),
                "บันทึกการรักษา",
                size="1",
                variant="soft",
                on_click=AppState.open_patient_record(a["patient_id"], "/records"),
            ),
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon(tag="file_text", size=14),
                size="1",
                variant="soft",
                color_scheme="gray",
                on_click=AppState.open_patient_record(a["patient_id"], "/records/summary"),
            ),
            content="ดูเวชระเบียน",
        ),
        spacing="2",
        wrap="wrap",
    )


def patient_row(a) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(a["time"], weight="bold", color="var(--primary-color)")),
        rx.table.cell(
            rx.vstack(
                rx.text(a["patient_name"], weight="medium"),
                rx.text(a["patient_id"] + " · " + a["phone"], size="1", color="var(--slate-10)"),
                medical_flags(a["disease"], a["allergy"]),
                spacing="1",
            )
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(a["service"], size="2"),
                rx.cond(a["purpose"] != "", rx.text(a["purpose"], size="1", color="var(--slate-10)")),
                spacing="0",
            )
        ),
        rx.table.cell(rx.cond(a["dentist"] != "", a["dentist"], rx.text("ยังไม่ระบุ", color="var(--slate-9)"))),
        rx.table.cell(rx.badge(a["kind"], variant="outline", color_scheme=rx.cond(a["kind"] == "นัดครั้งถัดไป", "purple", "cyan"))),
        rx.table.cell(status_badge(a["status"])),
        rx.table.cell(row_actions(a)),
        align="center",
    )


def patient_card(a) -> rx.Component:
    """Phone layout of one row of the daily table."""
    return rx.box(
        rx.hstack(
            rx.text(a["time"], weight="bold", size="4", color="var(--primary-color)"),
            rx.badge(a["kind"], variant="outline", color_scheme=rx.cond(a["kind"] == "นัดครั้งถัดไป", "purple", "cyan")),
            rx.spacer(),
            status_badge(a["status"]),
            align="center",
            width="100%",
        ),
        rx.text(a["patient_name"], weight="bold", margin_top="6px"),
        rx.text(a["patient_id"] + " · " + a["phone"], size="1", color="var(--slate-10)"),
        rx.text(a["service"], size="2", margin_top="4px"),
        rx.text(rx.cond(a["dentist"] != "", a["dentist"], "ทันตแพทย์: ยังไม่ระบุ"), size="1", color="var(--slate-10)"),
        rx.cond(a["purpose"] != "", rx.text(a["purpose"], size="1", color="var(--slate-10)")),
        rx.box(medical_flags(a["disease"], a["allergy"]), margin_top="6px"),
        rx.box(row_actions(a), margin_top="10px"),
        padding="12px",
        border="1px solid var(--slate-4)",
        border_radius="12px",
        background_color="white",
        width="100%",
    )


<<<<<<< HEAD
@rx.page(route="/dashboard", title="แดชบอร์ด", on_load=AppState.load_schedule_data)
def dashboard():
=======
@rx.page(
    route="/dashboard",
    title="แดชบอร์ดผู้ป่วยรายวัน - Dental Guardian",
    on_load=[AppState.check_staff_access, AppState.load_schedule_data],
)
def dashboard() -> rx.Component:
>>>>>>> origin/feat/backend-auth-v2
    s = AppState.daily_stats
    return staff_page(
        "dashboard",
        page_header(
            "แดชบอร์ดผู้ป่วยรายวัน",
            "รายชื่อผู้ป่วยที่จองคิวและมีนัดในแต่ละวัน",
            rx.hstack(
                rx.icon_button(rx.icon(tag="chevron_left"), variant="soft", on_click=AppState.shift_dashboard_date(-1)),
                rx.input(type="date", value=AppState.dashboard_date, on_change=AppState.set_dashboard_date, size="2"),
                rx.icon_button(rx.icon(tag="chevron_right"), variant="soft", on_click=AppState.shift_dashboard_date(1)),
                rx.button("วันนี้", variant="soft", on_click=AppState.set_dashboard_date(AppState.today_iso)),
                spacing="2",
                align="center",
            ),
        ),
        rx.grid(
            stat("ผู้ป่วยทั้งหมด", s["total"], "users", "blue"),
            stat("มาตามนัดแล้ว", s["arrived"], "user_check", "green"),
            stat("ยังไม่มา", s["waiting"], "clock", "orange"),
            stat("รออนุมัติ", s["pending"], "inbox", "amber"),
            stat("ยกเลิก", s["cancelled"], "calendar_x", "gray"),
            columns={"initial": "2", "md": "3", "lg": "5"},
            spacing="3",
            width="100%",
        ),
        card(
            card_title("ผู้ป่วยประจำวันที่ " + AppState.dashboard_date_th),
            rx.cond(
                AppState.daily_patients.length() > 0,
                rx.fragment(
                    rx.box(
                        table_wrap(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        *[
                                            rx.table.column_header_cell(h)
                                            for h in ["เวลา", "ผู้ป่วย", "บริการ", "ทันตแพทย์", "ประเภท", "สถานะ", "จัดการ"]
                                        ]
                                    ),
                                ),
                                rx.table.body(rx.foreach(AppState.daily_patients, patient_row)),
                                width="100%",
                            )
                        ),
                        display=["none", "none", "block"],
                        width="100%",
                    ),
                    rx.vstack(
                        rx.foreach(AppState.daily_patients, patient_card),
                        spacing="2",
                        width="100%",
                        display=["flex", "flex", "none"],
                    ),
                ),
                empty_state("ไม่มีผู้ป่วยในวันนี้", "calendar_x"),
            ),
        ),
    )