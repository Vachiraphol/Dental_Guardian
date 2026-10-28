"""SRS 5.3 (พนักงาน): หน้าจัดการนัดหมายคนไข้ — มาตามนัด / ยกเลิก / เลื่อนนัด / ออกใบนัดครั้งถัดไป."""

import reflex as rx

from dental_clinic_system.components.layout import staff_page
from dental_clinic_system.components.slip import slip_dialog
from dental_clinic_system.components.ui import card, empty_state, field, medical_flags, page_header, status_badge, table_wrap
from dental_clinic_system.state import SERVICES, TIME_OPTIONS, AppState

FILTERS = ["ทั้งหมด", "วันนี้", "ที่จะถึง", "ยืนยันแล้ว", "มาตามนัด", "เลื่อนนัด", "ยกเลิกนัด"]


def appt_actions(a, max_width: str = "230px") -> rx.Component:
    active = (a["status"] == "ยืนยันแล้ว") | (a["status"] == "เลื่อนนัด")
    return rx.flex(
        rx.cond(active, rx.button("มาตามนัด", size="1", color_scheme="green", on_click=AppState.mark_arrived(a["id"]))),
        rx.cond(active, rx.button("เลื่อนนัด", size="1", variant="soft", color_scheme="purple", on_click=AppState.open_reschedule(a["id"]))),
        rx.cond(active, rx.button("ยกเลิกนัด", size="1", variant="soft", color_scheme="red", on_click=AppState.cancel_appt(a["id"]))),
        rx.button("ใบนัด", size="1", variant="soft", on_click=AppState.show_slip(a["id"])),
        rx.cond(a["status"] == "มาตามนัด",
                rx.button("นัดครั้งถัดไป", size="1", variant="soft", color_scheme="blue", on_click=AppState.open_next_appt(a["patient_id"]))),
        gap="6px",
        wrap="wrap",
        max_width=max_width,
    )


def appt_card(a) -> rx.Component:
    """Phone layout of one appointment row."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(a["date_th"], weight="bold", size="2"),
                rx.text(a["time"] + " น.", weight="bold", size="4", color="var(--primary-color)"),
                spacing="0",
            ),
            rx.spacer(),
            rx.vstack(status_badge(a["status"]), rx.badge(a["id"], color_scheme="gray"), align="end", spacing="1"),
            width="100%",
            align="start",
        ),
        rx.text(a["patient_name"], weight="bold", margin_top="6px"),
        rx.text(a["phone"] + " · " + a["dentist"], size="1", color="var(--slate-10)"),
        rx.text(a["service"], size="2", margin_top="4px"),
        rx.cond(a["purpose"] != "", rx.text("เพื่อ: " + a["purpose"], size="1", color="var(--slate-10)")),
        rx.cond(a["reason"] != "", rx.text("หมายเหตุ: " + a["reason"], size="1", color="var(--slate-10)")),
        rx.box(medical_flags(a["disease"], a["allergy"]), margin_top="6px"),
        rx.box(appt_actions(a, "100%"), margin_top="10px"),
        padding="12px",
        border="1px solid var(--slate-4)",
        border_radius="12px",
        background_color="white",
        width="100%",
    )


def appt_row(a) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.vstack(rx.badge(a["id"], color_scheme="gray"),
                                rx.badge(a["kind"], variant="outline", color_scheme=rx.cond(a["kind"] == "นัดครั้งถัดไป", "purple", "cyan")),
                                spacing="1")),
        rx.table.cell(rx.vstack(rx.text(a["date_th"], size="2", weight="medium"), rx.text(a["time"] + " น.", size="1", color="var(--slate-10)"), spacing="0")),
        rx.table.cell(
            rx.vstack(
                rx.text(a["patient_name"], weight="medium"),
                rx.text(a["phone"], size="1", color="var(--slate-10)"),
                medical_flags(a["disease"], a["allergy"]),
                spacing="1",
            )
        ),
        rx.table.cell(rx.vstack(rx.text(a["service"], size="2"),
                                rx.cond(a["purpose"] != "", rx.text("เพื่อ: " + a["purpose"], size="1", color="var(--slate-10)")), spacing="0")),
        rx.table.cell(a["dentist"]),
        rx.table.cell(rx.vstack(status_badge(a["status"]),
                                rx.cond(a["reason"] != "", rx.text(a["reason"], size="1", color="var(--slate-10)")), spacing="1")),
        rx.table.cell(appt_actions(a)),
        align="center",
    )


def reschedule_dialog() -> rx.Component:
    t = AppState.resched_target
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("เลื่อนนัด " + t["id"]),
            rx.dialog.description(t["patient_name"] + " · เดิม " + t["date_th"] + " " + t["time"] + " น.", size="2", color="var(--slate-10)"),
            rx.form(
                rx.vstack(
                    rx.grid(
                        field("วันที่ใหม่", rx.input(name="date", type="date", default_value=t["date"], min=AppState.today_iso, required=True), True),
                        field("เวลาใหม่", rx.select(TIME_OPTIONS, name="time", default_value=t["time"], width="100%")),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),
                    field("เหตุผลที่เลื่อน", rx.input(name="reason", placeholder="เช่น ผู้ป่วยติดธุระ / ทันตแพทย์ลา")),
                    rx.hstack(
                        rx.dialog.close(rx.button("ยกเลิก", type="button", variant="soft", color_scheme="gray")),
                        rx.button("บันทึกการเลื่อนนัด", type="submit", color_scheme="purple"),
                        justify="end",
                        width="100%",
                        spacing="2",
                    ),
                    spacing="3",
                    width="100%",
                    margin_top="12px",
                ),
                on_submit=AppState.reschedule,
                key=t["id"],
            ),
            max_width="480px",
        ),
        open=AppState.resched_open,
        on_open_change=AppState.set_resched_open,
    )


def next_appt_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("ออกใบนัดครั้งถัดไป"),
            rx.dialog.description("หมอฟันบันทึกการนัดหมายครั้งถัดไป ผู้ป่วยจะเห็นนัดนี้ในหน้าตารางนัดหมายของฉัน", size="2", color="var(--slate-10)"),
            rx.form(
                rx.vstack(
                    field("ผู้ป่วย", rx.select(AppState.patient_options, name="patient", placeholder="เลือกผู้ป่วย", width="100%",
                                             default_value=AppState.next_appt_option), True),
                    rx.grid(
                        field("วันที่", rx.input(name="date", type="date", min=AppState.today_iso, required=True), True),
                        field("เวลา", rx.select(TIME_OPTIONS, name="time", default_value="10:00", width="100%")),
                        field("บริการ", rx.select(SERVICES, name="service", default_value=SERVICES[0], width="100%")),
                        field("ทันตแพทย์", rx.select(AppState.dentist_names, name="dentist", placeholder="เลือกทันตแพทย์", width="100%")),
                        columns={"initial": "1", "sm": "2"},
                        spacing="3",
                        width="100%",
                    ),
                    field("รายละเอียด (นัดเพื่ออะไร)", rx.text_area(name="purpose", rows="2", placeholder="เช่น รักษารากฟันซี่ 30 ครั้งที่ 2", required=True), True),
                    rx.hstack(
                        rx.dialog.close(rx.button("ยกเลิก", type="button", variant="soft", color_scheme="gray")),
                        rx.button("สร้างใบนัด", type="submit", color_scheme="purple"),
                        justify="end",
                        width="100%",
                        spacing="2",
                    ),
                    spacing="3",
                    width="100%",
                    margin_top="12px",
                ),
                on_submit=AppState.create_next_appt,
                key=AppState.next_appt_patient,
            ),
            max_width="560px",
        ),
        open=AppState.next_appt_open,
        on_open_change=AppState.set_next_appt_open,
    )


@rx.page(route="/appointments", title="จัดการนัดหมายคนไข้", on_load=AppState.load_schedule_data)
def appointments():
    return staff_page(
        "appointments",
        page_header(
            "จัดการนัดหมายคนไข้",
            "อัปเดตสถานะนัดหมาย (มาตามนัด / เลื่อนนัด / ยกเลิกนัด) และออกใบนัดครั้งถัดไป",
            rx.button(rx.icon(tag="calendar_plus", size=14), "ออกใบนัดครั้งถัดไป", color_scheme="purple", on_click=AppState.open_next_appt("")),
        ),
        card(
            rx.flex(
                rx.input(
                    rx.input.slot(rx.icon(tag="search", size=16)),
                    placeholder="ค้นหาชื่อผู้ป่วย เบอร์โทร หรือเลขที่นัด",
                    value=AppState.appt_search,
                    on_change=AppState.set_appt_search,
                    size="2",
                    flex="1",
                    min_width="220px",
                ),
                rx.box(
                    rx.segmented_control.root(
                        *[rx.segmented_control.item(f, value=f) for f in FILTERS],
                        value=AppState.appt_filter,
                        on_change=AppState.set_appt_filter,
                        size="1",
                    ),
                    max_width="100%",
                    overflow_x="auto",
                    class_name="dg-scroll-x",
                ),
                gap="12px",
                wrap="wrap",
                align="center",
                width="100%",
                margin_bottom="12px",
            ),
            rx.box(
                table_wrap(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(*[rx.table.column_header_cell(h) for h in ["เลขที่", "วัน/เวลา", "ผู้ป่วย", "รายละเอียด", "ทันตแพทย์", "สถานะ", "จัดการ"]]),
                        ),
                        rx.table.body(rx.foreach(AppState.managed_appointments, appt_row)),
                        width="100%",
                    )
                ),
                display=["none", "none", "block"],
                width="100%",
            ),
            rx.vstack(rx.foreach(AppState.managed_appointments, appt_card), spacing="2", width="100%",
                      display=["flex", "flex", "none"]),
            rx.cond(AppState.managed_appointments.length() == 0, empty_state("ไม่พบนัดหมาย", "calendar_search")),
        ),
        reschedule_dialog(),
        next_appt_dialog(),
        slip_dialog(),
    )
