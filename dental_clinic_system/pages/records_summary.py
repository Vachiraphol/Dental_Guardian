"""SRS 5.4 (พนักงาน) หน้าสรุปประวัติเวชระเบียนรวม."""

import reflex as rx

from dental_clinic_system.components.dental_chart import dental_chart
from dental_clinic_system.components.history import chart_badge, patient_picker
from dental_clinic_system.components.layout import staff_page
from dental_clinic_system.components.ui import card, card_title, empty_state, info_row, page_header, status_badge, table_wrap
from dental_clinic_system.state import AppState


def summary_stat(label: str, value) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--slate-10)"),
        rx.text(value, size="5", weight="bold"),
        spacing="0",
        padding="12px",
        border_radius="10px",
        background_color="var(--slate-2)",
        width="100%",
    )


@rx.page(route="/records/summary", title="สรุปประวัติเวชระเบียนรวม - Dental Guardian", on_load=AppState.load_schedule_data)
def records_summary() -> rx.Component:
    p = AppState.selected_patient
    s = AppState.sel_summary
    return staff_page(
        "summary",
        page_header(
            "สรุปประวัติเวชระเบียนรวม",
            "ข้อมูลผู้ป่วย ผังฟัน การวินิจฉัย และการนัดหมายทั้งหมดในหน้าเดียว",
            rx.button(rx.icon(tag="clipboard_pen", size=14), "บันทึกการรักษา", variant="soft", color_scheme="green",
                      on_click=AppState.open_patient_record(AppState.selected_pid, "/records")),
            rx.button(rx.icon(tag="printer", size=14), "พิมพ์", variant="soft", on_click=rx.call_script("window.print()")),
        ),
        patient_picker(),
        rx.cond(
            AppState.has_patients,
            rx.vstack(
                rx.grid(
                    summary_stat("จำนวนครั้งที่มารักษา", s["visits"]),
                    summary_stat("ซี่ฟันที่เคยรักษา", s["teeth"]),
                    summary_stat("รายการบันทึก", s["entries"]),
                    summary_stat("มาครั้งล่าสุด", s["last_visit"]),
                    summary_stat("นัดครั้งถัดไป", s["next"]),
                    summary_stat("ยกเลิกนัด", s["no_show"]),
                    columns={"initial": "2", "md": "3", "lg": "6"},
                    spacing="3",
                    width="100%",
                ),
                rx.flex(
                    card(
                        card_title("ข้อมูลผู้ป่วย"),
                        info_row("วันเกิด", p["dob_th"]),
                        info_row("เลขบัตรประชาชน", p["national_id"]),
                        info_row("เบอร์โทรศัพท์", p["phone"]),
                        info_row("อีเมล", p["email"]),
                        info_row("ที่อยู่", p["address"]),
                        info_row("โรคประจำตัว", p["disease"]),
                        info_row("ยาที่แพ้", p["allergy"]),
                        info_row("สมาชิกตั้งแต่", p["registered_th"]),
                        flex="1",
                        min_width="0",
                    ),
                    card(
                        card_title("ผังฟัน", chart_badge()),
                        dental_chart(AppState.sel_treated_teeth, AppState.selected_tooth, AppState.select_tooth),
                        card_title("การวินิจฉัยที่พบ"),
                        rx.flex(
                            rx.foreach(
                                AppState.sel_diagnoses,
                                lambda d: rx.badge(d["code"] + " " + d["th"] + " × " + d["count"], variant="soft", color_scheme="blue", size="2"),
                            ),
                            gap="6px",
                            wrap="wrap",
                        ),
                        flex="2",
                        min_width="0",
                    ),
                    direction={"initial": "column", "lg": "row"},
                    gap="16px",
                    align="start",
                    width="100%",
                ),
                card(
                    card_title("ประวัติการรักษาทั้งหมด"),
                    table_wrap(
                        rx.table.root(
                            rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in
                                                           ["วัน/เวลา", "ซี่ฟัน", "การวินิจฉัย (ICD-10)", "การรักษา", "หมายเหตุ", "ทันตแพทย์"]])),
                            rx.table.body(
                                rx.foreach(
                                    AppState.sel_entries,
                                    lambda e: rx.table.row(
                                        rx.table.cell(e["ts_th"]),
                                        rx.table.cell(rx.badge(e["tooth"], color_scheme="purple")),
                                        rx.table.cell(rx.vstack(rx.text(e["icd_th"], size="2"), rx.text(e["icd"], size="1", color="var(--slate-10)"), spacing="0")),
                                        rx.table.cell(e["procedure"]),
                                        rx.table.cell(rx.text(e["note"], size="2", max_width="280px")),
                                        rx.table.cell(e["dentist"]),
                                    ),
                                )
                            ),
                            width="100%",
                        )
                    ),
                    rx.cond(AppState.sel_entries.length() == 0, empty_state("ยังไม่มีประวัติการรักษา", "clipboard")),
                ),
                card(
                    card_title("ประวัติการนัดหมาย"),
                    rx.cond(
                        AppState.sel_appointments.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                AppState.sel_appointments,
                                lambda a: rx.hstack(
                                    rx.text(a["date_th"] + " " + a["time"], size="2", weight="medium", min_width="150px"),
                                    rx.text(a["service"], size="2"),
                                    rx.cond(a["purpose"] != "", rx.text("· " + a["purpose"], size="1", color="var(--slate-10)")),
                                    rx.spacer(),
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
                        empty_state("ยังไม่มีนัดหมาย", "calendar"),
                    ),
                ),
                width="100%",
                spacing="4",
            ),
            card(empty_state("ยังไม่มีผู้ป่วยในระบบ — ผู้ป่วยต้องสมัครสมาชิกหรือจองคิวผ่านเว็บไซต์ก่อน", "users")),
        ),
    )
