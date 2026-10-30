"""SRS 5.3: หน้าตั้งค่าและแสดงตารางเวลาปฏิบัติงานทันตแพทย์รายสัปดาห์."""

import reflex as rx

from dental_clinic_system.components.layout import staff_page
from dental_clinic_system.components.ui import card, card_title, empty_state, field, page_header
from dental_clinic_system.state import THAI_DAYS_FULL, TIME_OPTIONS, AppState


def dentist_tab(d) -> rx.Component:
    selected = AppState.schedule_dentist_id == d["id"]
    return rx.hstack(
        rx.avatar(fallback=d["name"][4:6], size="3", radius="full", color_scheme="purple"),
        rx.vstack(
            rx.text(d["name"], weight="bold", size="2"),
            rx.text(
                rx.cond(d.contains("specialty") & (d["specialty"] != ""), d["specialty"], "ทันตแพทย์"),
                size="1",
                color="var(--slate-10)",
            ),
            spacing="0",
        ),
        align="center",
        padding="12px",
        border_radius="12px",
        border=rx.cond(selected, "2px solid var(--purple-9)", "1px solid var(--slate-5)"),
        background_color=rx.cond(selected, "var(--primary-light)", "white"),
        cursor="pointer",
        on_click=AppState.select_schedule_dentist(d["id"]),
        width="100%",
    )


def day_toggle(i: int, name: str) -> rx.Component:
    on = AppState.schedule_days.contains(str(i))
    return rx.button(
        name,
        variant=rx.cond(on, "solid", "outline"),
        color_scheme=rx.cond(on, "purple", "gray"),
        on_click=AppState.toggle_work_day(str(i)),
        width="100%",
    )


def monthly_calendar_view() -> rx.Component:
    """ปฏิทินรายเดือนแบบตาราง 7 คอลัมน์ (จันทร์-อาทิตย์) แสดงวันที่ 1 ถึงวันสิ้นเดือนจริง"""
    day_headers = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

    return card(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="calendar_days", size=22, color="var(--purple-9)"),
                rx.heading(
                    rx.cond(
                        AppState.user_role == "dentist",
                        "ตารางเวลาปฏิบัติงานประจำเดือนของคุณ",
                        "ตารางเวลาปฏิบัติงานของ " + rx.cond(AppState.schedule_dentist.contains("name"), AppState.schedule_dentist["name"], "ทันตแพทย์"),
                    ),
                    size="4",
                    weight="bold",
                ),
                align="center",
                spacing="2",
            ),
            rx.text(
                "ตารางแสดงวันและเวลาปฏิบัติงานตลอดทั้งเดือน เรียงตามวันที่ 1 จนถึงสิ้นเดือน",
                size="2",
                color="var(--slate-10)",
            ),
            # หัวตาราง จันทร์ - อาทิตย์
            rx.grid(
                *[
                    rx.center(
                        rx.text(d_name, weight="bold", size="2", color="var(--slate-11)"),
                        padding_y="8px",
                        background_color="var(--slate-3)",
                        border_radius="8px",
                    )
                    for d_name in day_headers
                ],
                columns="7",
                spacing="2",
                width="100%",
                margin_top="12px",
            ),
            # ช่องวันที่ 1 ถึง 28/29/30/31
            rx.grid(
                rx.foreach(
                    AppState.monthly_calendar_days,
                    lambda cell: rx.cond(
                        cell["is_empty"],
                        # ช่องว่างต้นเดือน
                        rx.box(width="100%", height="84px"),
                        # ช่องวันที่มีวันที่จริง
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.text(cell["day_num"], weight="bold", size="3", color="var(--slate-12)"),
                                    rx.spacer(),
                                    rx.cond(
                                        cell["is_leave"],
                                        rx.badge("ลาหยุด", color_scheme="red", variant="solid", size="1"),
                                        rx.cond(
                                            cell["is_work"] == "1",
                                            rx.badge("เข้าเวร", color_scheme="green", variant="soft", size="1"),
                                            rx.badge("หยุด", color_scheme="gray", variant="soft", size="1"),
                                        ),
                                    ),
                                    width="100%",
                                    align="center",
                                ),
                                rx.divider(margin_y="4px"),
                                rx.cond(
                                    cell["is_leave"],
                                    rx.text(cell["leave_reason"], size="1", color="var(--red-9)", weight="medium", no_of_lines=1),
                                    rx.cond(
                                        cell["is_work"] == "1",
                                        rx.text(cell["time"], size="1", weight="bold", color=cell["text_color"]),
                                        rx.text("-", size="1", color="var(--slate-8)"),
                                    ),
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            padding="10px",
                            border_radius="10px",
                            background_color=cell["bg"],
                            border=f"1.5px solid {cell['border']}",
                            width="100%",
                            min_height="84px",
                        ),
                    ),
                ),
                columns="7",
                spacing="2",
                width="100%",
            ),
            width="100%",
            spacing="2",
        ),
        padding="18px",
        margin_bottom="20px",
    )


@rx.page(
    route="/schedule",
    title="ตารางเวลาปฏิบัติงานทันตแพทย์ - Dental Guardian",
    on_load=[AppState.check_staff_access, AppState.load_schedule_data],
)
def schedule() -> rx.Component:
    d = AppState.schedule_dentist
    is_staff = (AppState.user_role == "staff") | (AppState.user_role == "admin")

    return staff_page(
        "schedule",
        page_header(
            "ตารางเวลาปฏิบัติงานทันตแพทย์",
            "ตรวจสอบและจัดการเวลาเข้าเวรตรวจของทันตแพทย์แต่ละท่าน",
            rx.cond(
                is_staff,
                rx.button(
                    rx.icon(tag="save", size=14),
                    "บันทึกตารางเวลา",
                    color_scheme="purple",
                    on_click=AppState.save_schedule,
                ),
                rx.fragment(),
            ),
        ),
        # แถบเลือกเดือนสำหรับจัดตารางงาน
        rx.hstack(
            rx.text("เลือกเดือนตารางงาน:", weight="bold", size="2"),
            rx.select(
                ["2026-10", "2026-11", "2026-12", "2027-01"],
                value=AppState.schedule_selected_month,
                on_change=AppState.set_schedule_selected_month,
                size="2",
            ),
            align="center",
            spacing="2",
            margin_bottom="16px",
        ),
        # 1. แสดงปฏิทินตารางงานแยกสี จันทร์-อาทิตย์ พร้อมวันที่จริง
        monthly_calendar_view(),
        # 2. ส่วนตั้งค่า: แสดงเฉพาะเมื่อสตาฟหรือแอดมินเป็นคนล็อกอินเข้ามาจัดตาราง
        rx.cond(
            is_staff,
            rx.grid(
                rx.vstack(
                    card(
                        card_title("เลือกทันตแพทย์"),
                        rx.cond(
                            AppState.dentists.length() > 0,
                            rx.vstack(rx.foreach(AppState.dentists, dentist_tab), width="100%", spacing="2"),
                            empty_state("ยังไม่มีข้อมูลทันตแพทย์", "user_x"),
                        ),
                    ),
                    card(
                        card_title("ภาพรวมรายสัปดาห์"),
                        rx.vstack(
                            rx.foreach(
                                AppState.week_overview,
                                lambda r: rx.hstack(
                                    rx.text(r["day"], size="2", weight="medium", min_width="70px"),
                                    rx.text(
                                        r["dentists"],
                                        size="1",
                                        color=rx.cond(r["open"] == "1", "var(--slate-11)", "var(--red-10)"),
                                    ),
                                    width="100%",
                                    padding_y="6px",
                                    border_bottom="1px solid var(--slate-3)",
                                ),
                            ),
                            width="100%",
                            spacing="0",
                        ),
                    ),
                    width="100%",
                    spacing="4",
                ),
                rx.vstack(
                    card(
                        card_title("วันเข้าเวรของ " + rx.cond(d.contains("name"), d["name"], "ทันตแพทย์")),
                        rx.grid(
                            *[day_toggle(i, name) for i, name in enumerate(THAI_DAYS_FULL, start=1)],
                            columns={"initial": "4", "sm": "7"},
                            spacing="2",
                            width="100%",
                        ),
                    ),
                    card(
                        card_title("เวลาทำงาน"),
                        rx.grid(
                            field("เริ่มงาน", rx.select(TIME_OPTIONS, value=d["start"], on_change=AppState.set_sched_start, width="100%")),
                            field("เลิกงาน", rx.select(TIME_OPTIONS, value=d["end"], on_change=AppState.set_sched_end, width="100%")),
                            field(
                                "พักกลางวัน (1 ชม.)",
                                rx.select(
                                    ["ไม่มีพัก"] + TIME_OPTIONS,
                                    value=rx.cond(d.contains("lunch") & (d["lunch"] != ""), d["lunch"], "ไม่มีพัก"),
                                    on_change=AppState.set_sched_lunch,
                                    width="100%",
                                ),
                            ),
                            columns={"initial": "1", "sm": "3"},
                            spacing="3",
                            width="100%",
                        ),
                        rx.text("ช่วงเวลารับคิวตรวจ (ช่องละ 30 นาที)", size="2", weight="medium", margin_top="16px", margin_bottom="8px"),
                        rx.flex(
                            rx.foreach(AppState.schedule_preview, lambda t: rx.badge(t, variant="soft", color_scheme="purple")),
                            gap="6px",
                            wrap="wrap",
                        ),
                    ),
                    card(
                        card_title("วันลา / วันหยุดพิเศษ"),
                        rx.hstack(
                            rx.input(
                                type="date",
                                value=AppState.new_leave_date,
                                on_change=AppState.set_new_leave_date,
                                size="2",
                                width="170px",
                                custom_attrs={"min": AppState.today_iso},
                            ),
                            rx.input(
                                placeholder="รายละเอียด เช่น ลาพักร้อน, ประชุมสัมมนา",
                                value=AppState.new_leave_reason,
                                on_change=AppState.set_new_leave_reason,
                                size="2",
                                flex="1",
                            ),
                            rx.button(
                                rx.icon(tag="plus", size=14),
                                "เพิ่มวันหยุด",
                                variant="soft",
                                color_scheme="purple",
                                on_click=AppState.add_leave,
                                size="2",
                                white_space="nowrap",
                            ),
                            width="100%",
                            spacing="2",
                            align="center",
                            margin_bottom="12px",
                        ),
                        rx.cond(
                            AppState.schedule_leaves.length() > 0,
                            rx.flex(
                                rx.foreach(
                                    AppState.schedule_leaves,
                                    lambda leave: rx.badge(
                                        rx.hstack(
                                            rx.icon(tag="calendar-off", size=12),
                                            rx.text(leave["label"], size="2", weight="medium"),
                                            rx.icon(
                                                tag="x",
                                                size=12,
                                                cursor="pointer",
                                                on_click=AppState.remove_leave(leave["date"]),
                                            ),
                                            spacing="1",
                                            align="center",
                                        ),
                                        color_scheme="red",
                                        variant="soft",
                                        padding_x="8px",
                                        padding_y="4px",
                                        radius="full",
                                    ),
                                ),
                                gap="6px",
                                wrap="wrap",
                            ),
                            empty_state("ไม่มีวันลา / วันหยุดพิเศษในเดือนนี้", "calendar_check"),
                        ),
                    ),
                    width="100%",
                    spacing="4",
                    grid_column={"initial": "span 1", "lg": "span 2"},
                ),
                columns={"initial": "1", "lg": "3"},
                spacing="4",
                width="100%",
            ),
            rx.fragment(),
        ),
    )