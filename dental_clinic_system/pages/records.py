"""SRS 5.4 (พนักงาน) หน้าบันทึกการรักษาและผังฟัน."""

import reflex as rx

from dental_clinic_system.components.dental_chart import dental_chart
from dental_clinic_system.components.history import chart_badge, entry_item, patient_picker
from dental_clinic_system.components.layout import staff_page
from dental_clinic_system.components.ui import card, card_title, empty_state, field, page_header
from dental_clinic_system.state import (
    AppState,
    ICD10,
    PERMANENT_LOWER,
    PERMANENT_UPPER,
    PRIMARY_TEETH_LOWER,
    PRIMARY_TEETH_UPPER,
    PROCEDURES,
    tooth_label,
)


def tooth_picker() -> rx.Component:
    is_child = AppState.chart_mode == "child"

    adult_select_content = rx.select.content(
        rx.select.group(
            rx.select.label("ขากรรไกรบน (16 ซี่)"),
            *[rx.select.item(tooth_label(t), value=t) for t in PERMANENT_UPPER],
        ),
        rx.select.separator(),
        rx.select.group(
            rx.select.label("ขากรรไกรล่าง (16 ซี่)"),
            *[rx.select.item(tooth_label(t), value=t) for t in PERMANENT_LOWER],
        ),
    )

    child_select_content = rx.select.content(
        rx.select.group(
            rx.select.label("ขากรรไกรบน (ฟันน้ำนม 10 ซี่)"),
            *[rx.select.item(tooth_label(t), value=t) for t in PRIMARY_TEETH_UPPER],
        ),
        rx.select.separator(),
        rx.select.group(
            rx.select.label("ขากรรไกรล่าง (ฟันน้ำนม 10 ซี่)"),
            *[rx.select.item(tooth_label(t), value=t) for t in PRIMARY_TEETH_LOWER],
        ),
    )

    return rx.vstack(
        rx.hstack(
            rx.text("ซี่ฟัน", size="2", weight="medium"),
            rx.text.span(" *", color="var(--red-9)"),
            rx.spacer(),
            rx.segmented_control.root(
                rx.segmented_control.item("Dropdown", value="dropdown"),
                rx.segmented_control.item("พิมพ์เอง", value="type"),
                value=AppState.tooth_input_mode,
                on_change=AppState.set_tooth_input_mode,
                size="1",
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            AppState.tooth_input_mode == "dropdown",
            rx.select.root(
                rx.select.trigger(placeholder="เลือกซี่ฟัน หรือคลิกที่ผังฟัน", width="100%"),
                rx.cond(is_child, child_select_content, adult_select_content),
                value=AppState.entry_tooth,
                on_change=AppState.set_entry_tooth,
                size="3",
            ),
            rx.input(
                placeholder=rx.cond(is_child, "พิมพ์เลขซี่ฟันน้ำนม เช่น 51, 85", "พิมพ์เลขซี่ฟัน 11–48 เช่น 18"),
                value=AppState.entry_tooth,
                on_change=AppState.set_entry_tooth,
                size="3",
                max_length=2,
                width="100%",
            ),
        ),
        rx.text(AppState.entry_tooth_label, size="1", color="var(--primary-color)"),
        width="100%",
        spacing="1",
    )


def entry_form() -> rx.Component:
    info = AppState.entry_icd_info
    return card(
        card_title("บันทึกการรักษา"),
        rx.vstack(
            tooth_picker(),
            field(
                "การวินิจฉัย (ICD-10)",
                rx.select.root(
                    rx.select.trigger(placeholder="เลือกรหัส ICD-10", width="100%"),
                    rx.select.content(*[rx.select.item(f"{code} — {th}", value=code) for code, th, _ in ICD10]),
                    value=AppState.entry_icd,
                    on_change=AppState.set_entry_icd,
                    size="3",
                ),
                True,
            ),
            rx.cond(
                AppState.has_entry_icd,
                rx.box(
                    rx.text("คำอธิบายสำหรับผู้ป่วย", size="1", color="var(--slate-10)"),
                    rx.text(info["th"], weight="bold"),
                    rx.text(info["code"] + " · " + info["en"], size="1", color="var(--slate-10)"),
                    padding="10px",
                    border_radius="8px",
                    background_color="var(--blue-2)",
                    border="1px solid var(--blue-5)",
                    width="100%",
                ),
            ),
            field("การรักษา / หัตถการ", rx.select(PROCEDURES, value=AppState.entry_procedure, on_change=AppState.set_entry_procedure,
                                                   size="3", width="100%")),
            field("หมายเหตุเพิ่มเติม", rx.text_area(value=AppState.entry_note, on_change=AppState.set_entry_note, rows="3",
                                                     placeholder="รายละเอียดการรักษา วัสดุที่ใช้ คำแนะนำ ฯลฯ")),
            rx.hstack(
                rx.icon(tag="clock", size=14, color="var(--slate-10)"),
                rx.text("วัน/เวลาที่บันทึกจะถูกระบุอัตโนมัติ · ผู้บันทึก: " + AppState.user_name, size="1", color="var(--slate-10)"),
                align="center",
            ),
            rx.button(rx.icon(tag="save", size=16), "บันทึกการรักษา", size="3", color_scheme="green", width="100%", on_click=AppState.save_entry),
            width="100%",
            spacing="3",
        ),
    )


@rx.page(route="/records", title="บันทึกการรักษาและผังฟัน - Dental Guardian")
def records() -> rx.Component:
    return staff_page(
        "records",
        page_header(
            "บันทึกการรักษาและผังฟัน",
            "คลิกซี่ฟันบนผัง หรือเลือก/พิมพ์เลขซี่ฟัน แล้วบันทึกการวินิจฉัยและการรักษา",
            rx.button(rx.icon(tag="file_text", size=14), "ดูเวชระเบียนรวม", variant="soft",
                      on_click=AppState.open_patient_record(AppState.selected_pid, "/records/summary")),
        ),
        patient_picker(),
        rx.cond(
            AppState.has_patients,
            rx.vstack(
                rx.flex(
                    rx.vstack(
                        card(
                            card_title("ผังฟัน", chart_badge()),
                            dental_chart(AppState.sel_treated_teeth, AppState.selected_tooth, AppState.select_tooth),
                        ),
                        card(
                            rx.cond(
                                AppState.selected_tooth != "",
                                card_title("ประวัติ " + AppState.selected_tooth_label),
                                card_title("ประวัติการรักษาล่าสุด"),
                            ),
                            rx.cond(
                                AppState.selected_tooth != "",
                                rx.cond(
                                    AppState.sel_tooth_entries.length() > 0,
                                    rx.vstack(rx.foreach(AppState.sel_tooth_entries, lambda e: entry_item(e, False)), width="100%", spacing="2"),
                                    empty_state("ซี่นี้ยังไม่มีประวัติการรักษา", "smile"),
                                ),
                                rx.cond(
                                    AppState.sel_entries.length() > 0,
                                    rx.vstack(rx.foreach(AppState.sel_entries, lambda e: entry_item(e)), width="100%", spacing="2"),
                                    empty_state("ยังไม่มีประวัติการรักษา", "clipboard"),
                                ),
                            ),
                        ),
                        width="100%",
                        spacing="4",
                        flex="2",
                        min_width="0",
                    ),
                    rx.box(entry_form(), flex="1", min_width="0", width="100%"),
                    direction={"initial": "column", "lg": "row"},
                    gap="16px",
                    align="start",
                    width="100%",
                ),
                width="100%",
                spacing="4",
            ),
            card(empty_state("ยังไม่มีผู้ป่วยในระบบ — ผู้ป่วยต้องสมัครสมาชิกหรือจองคิวผ่านเว็บไซต์ก่อน", "users")),
        ),
    )