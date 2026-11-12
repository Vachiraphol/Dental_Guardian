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

IMPORT_UPLOAD_ID = "chart_import"
IMPORT_MAX_BYTES = 2 * 1024 * 1024


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
            wrap="wrap",
            gap="12px",
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


def import_status(row) -> rx.Component:
    return rx.match(
        row["status"],
        ("ok", rx.badge("พร้อมนำเข้า", color_scheme="green", variant="soft")),
        ("dup", rx.badge("ซ้ำ · ข้าม", color_scheme="gray", variant="soft")),
        rx.badge("ต้องแก้ไข", color_scheme="red", variant="soft"),
    )


def import_row(row) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["row"]),
        rx.table.cell(row["date_th"]),
        rx.table.cell(row["tooth"]),
        rx.table.cell(row["icd"]),
        rx.table.cell(row["procedure"]),
        rx.table.cell(rx.text(row["note"], size="2", max_width="200px")),
        rx.table.cell(
            rx.vstack(
                import_status(row),
                rx.cond(row["message"] != "", rx.text(row["message"], size="1", color="var(--red-11)")),
                spacing="1",
            )
        ),
    )


def import_preview() -> rx.Component:
    counts = AppState.import_counts
    return rx.vstack(
        rx.hstack(
            rx.badge("พร้อมนำเข้า ", counts["ok"], color_scheme="green", variant="soft"),
            rx.badge("ซ้ำ ", counts["dup"], color_scheme="gray", variant="soft"),
            rx.badge("ต้องแก้ไข ", counts["error"], color_scheme="red", variant="soft"),
            spacing="2",
            wrap="wrap",
        ),
        rx.cond(
            AppState.import_teeth.length() > 0,
            rx.text("ซี่ฟันที่จะมีข้อมูลเพิ่ม: ", AppState.import_teeth.join(", "), size="2", color="#334155"),
        ),
        rx.cond(
            counts["error"] > 0,
            rx.callout(
                "แก้แถวที่มีปัญหาในไฟล์ แล้วอัปโหลดใหม่ ระบบจะยังไม่บันทึกข้อมูลใดๆ",
                icon="circle_alert",
                color_scheme="red",
                size="1",
                width="100%",
            ),
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[
                            rx.table.column_header_cell(h)
                            for h in ["แถว", "วันที่รักษา", "ซี่ฟัน", "ICD-10", "การรักษา", "หมายเหตุ", "สถานะ"]
                        ]
                    )
                ),
                rx.table.body(rx.foreach(AppState.import_rows, import_row)),
                size="1",
                width="100%",
            ),
            width="100%",
            max_height="320px",
            overflow="auto",
        ),
        width="100%",
        spacing="3",
    )


def import_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("นำเข้าไฟล์สู่ผังฟัน"),
            rx.dialog.description(
                "นำเข้าให้ผู้ป่วย: ",
                rx.text.strong(AppState.selected_patient_option),
                size="2",
                color="#334155",
            ),
            rx.vstack(
                rx.upload(
                    rx.vstack(
                        rx.icon(tag="file_up", size=24, color="#64748B"),
                        rx.text("ลากไฟล์มาวาง หรือคลิกเพื่อเลือกไฟล์", size="2", color="#334155"),
                        rx.text("รองรับ .csv และ .xlsx ไม่เกิน 2 MB", size="1", color="#64748B"),
                        align="center",
                        spacing="1",
                    ),
                    id=IMPORT_UPLOAD_ID,
                    accept={
                        "text/csv": [".csv"],
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                    },
                    multiple=False,
                    max_files=1,
                    max_size=IMPORT_MAX_BYTES,
                    on_drop=AppState.handle_chart_import(rx.upload_files(upload_id=IMPORT_UPLOAD_ID)),
                    on_drop_rejected=rx.toast.error("รองรับเฉพาะไฟล์ .csv และ .xlsx ขนาดไม่เกิน 2 MB ครั้งละ 1 ไฟล์"),
                    border="1px dashed #CBD5E1",
                    border_radius="12px",
                    padding="20px",
                    width="100%",
                    cursor="pointer",
                ),
                rx.text("คอลัมน์: วันที่รักษา, ซี่ฟัน (FDI), ICD-10, การรักษา, หมายเหตุ, ทันตแพทย์", size="1", color="#64748B"),
                rx.cond(AppState.import_file_name != "", rx.text("ไฟล์: " + AppState.import_file_name, size="2", color="#334155")),
                rx.cond(
                    AppState.import_error != "",
                    rx.callout(AppState.import_error, icon="circle_alert", color_scheme="red", size="1", width="100%"),
                ),
                rx.cond(AppState.import_rows.length() > 0, import_preview()),
                rx.hstack(
                    rx.dialog.close(rx.button("ยกเลิก", type="button", variant="soft", color_scheme="gray")),
                    rx.button(
                        "ยืนยันนำเข้า ",
                        AppState.import_counts["ok"],
                        " รายการ",
                        type="button",
                        color_scheme="green",
                        disabled=~AppState.can_confirm_import,
                        on_click=AppState.confirm_chart_import,
                    ),
                    justify="end",
                    width="100%",
                    spacing="2",
                ),
                width="100%",
                spacing="3",
                margin_top="12px",
            ),
            width="760px",
            max_width="calc(100vw - 32px)",
        ),
        open=AppState.import_open,
        on_open_change=AppState.set_import_open,
    )


@rx.page(
    route="/records",
    title="บันทึกการรักษาและผังฟัน - Dental Guardian",
    on_load=[AppState.check_clinical_access, AppState.load_patients_data, AppState.load_treatment_entries],
)
def records() -> rx.Component:
    return staff_page(
        "records",
        page_header(
            "บันทึกการรักษาและผังฟัน",
            "คลิกซี่ฟันบนผัง หรือเลือก/พิมพ์เลขซี่ฟัน แล้วบันทึกการวินิจฉัยและการรักษา",
            rx.cond(
                AppState.is_dentist & AppState.has_patients,
                rx.button(
                    rx.icon(tag="file_up", size=14),
                    "นำเข้าไฟล์",
                    variant="soft",
                    color_scheme="green",
                    on_click=AppState.set_import_open(True),
                ),
                rx.fragment(),
            ),
            rx.cond(
                AppState.user_role != "dentist",
                rx.button(
                    rx.icon(tag="file_text", size=14),
                    "ดูเวชระเบียนรวม",
                    variant="soft",
                    color_scheme="purple",
                    on_click=AppState.open_patient_record(AppState.selected_pid, "/records/summary"),
                ),
                rx.fragment(),
            ),
        ),
        import_dialog(),
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