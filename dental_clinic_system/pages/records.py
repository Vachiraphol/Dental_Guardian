"""SRS 5.4 (พนักงาน) หน้าบันทึกการรักษาและผังฟัน."""

import reflex as rx

from dental_clinic_system.components.dental_chart import dental_chart
from dental_clinic_system.components.history import chart_badge, entry_item, patient_picker
from dental_clinic_system.components.layout import staff_page
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


# --- Custom Light Theme Components สำหรับหน้านี้โดยเฉพาะ ---
def page_header(title: str, subtitle: str, *actions) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.heading(title, size="6", color="#0F172A", weight="bold"),
                rx.text(subtitle, size="2", color="#64748B"),
                spacing="1",
            ),
            rx.spacer(),
            *actions,
            align="center",
            width="100%",
        ),
        background_color="white",
        border="1px solid #E2E8F0",
        border_radius="16px",
        padding="20px 24px",
        box_shadow="0 4px 20px rgba(80, 60, 140, 0.04)",
        width="100%",
    )


def card(*children, **props) -> rx.Component:
    return rx.box(
        *children,
        background_color="white",
        border="1px solid #E2E8F0",
        border_radius="16px",
        padding="20px",
        box_shadow="0 4px 16px rgba(80, 60, 140, 0.04)",
        width="100%",
        **props,
    )


def card_title(title: str, *badges) -> rx.Component:
    return rx.hstack(
        rx.heading(title, size="4", color="#0F172A", weight="bold"),
        *badges,
        align="center",
        spacing="2",
        margin_bottom="12px",
    )


def empty_state(text: str, icon: str) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(tag=icon, size=28, color="#94A3B8"),
            rx.text(text, size="2", color="#64748B"),
            align="center",
            spacing="2",
            padding_y="24px",
        ),
        width="100%",
    )


def field(label: str, control: rx.Component, required: bool = False) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(label, size="2", weight="medium", color="#334155"),
            *([rx.text.span(" *", color="var(--red-9)")] if required else []),
            spacing="1",
        ),
        control,
        width="100%",
        spacing="1",
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
            rx.text("ซี่ฟัน", size="2", weight="medium", color="#334155"),
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
                    rx.text("คำอธิบายสำหรับผู้ป่วย", size="1", color="#64748B"),
                    rx.text(info["th"], weight="bold", color="#0F172A"),
                    rx.text(info["code"] + " · " + info["en"], size="1", color="#64748B"),
                    padding="10px",
                    border_radius="8px",
                    background_color="#EFF6FF",
                    border="1px solid #BFDBFE",
                    width="100%",
                ),
            ),
            field(
                "การรักษา / หัตถการ",
                rx.select.root(
                    rx.select.trigger(placeholder="เลือกหัตถการ", width="100%"),
                    rx.select.content(*[rx.select.item(p, value=p) for p in PROCEDURES]),
                    value=AppState.entry_procedure,
                    on_change=AppState.set_entry_procedure,
                    size="3",
                ),
            ),
            field(
                "หมายเหตุเพิ่มเติม",
                rx.text_area(
                    value=AppState.entry_note,
                    on_change=AppState.set_entry_note,
                    rows="3",
                    placeholder="รายละเอียดการรักษา วัสดุที่ใช้ คำแนะนำ ฯลฯ",
                ),
            ),
            rx.hstack(
                rx.icon(tag="clock", size=14, color="#64748B"),
                rx.text("วัน/เวลาที่บันทึกจะถูกระบุอัตโนมัติ · ผู้บันทึก: " + AppState.user_name, size="1", color="#64748B"),
                align="center",
            ),
            rx.button(
                rx.icon(tag="save", size=16),
                "บันทึกการรักษา",
                size="3",
                color_scheme="green",
                width="100%",
                on_click=AppState.save_entry,
            ),
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
            rx.button(
                rx.icon(tag="file_text", size=14),
                "ดูเวชระเบียนรวม",
                variant="soft",
                color_scheme="purple",
                on_click=AppState.open_patient_record(AppState.selected_pid, "/records/summary"),
            ),
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