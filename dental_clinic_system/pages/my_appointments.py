"""SRS 5.3 (ลูกค้า) หน้าตารางนัดหมายของฉัน."""

import reflex as rx

from dental_clinic_system.components.layout import member_page
from dental_clinic_system.components.slip import slip_dialog
from dental_clinic_system.components.ui import empty_state, page_header, status_badge
from dental_clinic_system.state import AppState


def appt_card(a, upcoming: bool) -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.text(a["weekday"], size="1", color="var(--slate-10)"),
            rx.text(a["date_th"], size="2", weight="bold"),
            rx.text(a["time"] + " น.", size="4", weight="bold", color="var(--primary-color)"),
            spacing="0",
            align="center",
            min_width="110px",
            padding="10px",
            border_radius="12px",
            background_color="var(--primary-light)",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(a["service"], weight="bold"),
                rx.badge(a["kind"], variant="outline", color_scheme=rx.cond(a["kind"] == "นัดครั้งถัดไป", "purple", "cyan")),
                status_badge(a["status"]),
                align="center",
                wrap="wrap",
            ),
            rx.text(rx.cond(a["dentist"] != "", a["dentist"], "ทันตแพทย์: รอคลินิกจัดให้"), size="2", color="var(--slate-11)"),
            rx.cond(a["purpose"] != "", rx.text("นัดเพื่อ: " + a["purpose"], size="2")),
            rx.cond(a["reason"] != "", rx.text("หมายเหตุ: " + a["reason"], size="1", color="var(--slate-10)")),
            rx.text("เลขที่ " + a["id"], size="1", color="var(--slate-9)"),
            spacing="1",
            align="start",
            flex="1",
        ),
        rx.flex(
            rx.button(rx.icon(tag="ticket", size=14), "ใบนัด", size="1", variant="soft", on_click=AppState.show_slip(a["id"])),
            *([
                rx.button(rx.icon(tag="calendar_plus", size=14), "ปฏิทิน", size="1", variant="soft", color_scheme="green",
                          on_click=AppState.download_ics(a["id"])),
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(rx.button("ยกเลิก", size="1", variant="soft", color_scheme="red")),
                    rx.alert_dialog.content(
                        rx.alert_dialog.title("ยกเลิกนัดหมายนี้?"),
                        rx.alert_dialog.description(rx.text(a["service"] + " · " + a["date_th"] + " " + a["time"] + " น.")),
                        rx.hstack(
                            rx.alert_dialog.cancel(rx.button("ไม่ยกเลิก", variant="soft", color_scheme="gray")),
                            rx.alert_dialog.action(rx.button("ยืนยันยกเลิก", color_scheme="red", on_click=AppState.cancel_my_appt(a["id"]))),
                            justify="end",
                            spacing="2",
                            margin_top="16px",
                        ),
                    ),
                ),
            ] if upcoming else []),
            direction={"initial": "row", "sm": "column"},
            gap="6px",
            wrap="wrap",
        ),
        width="100%",
        direction={"initial": "column", "sm": "row"},
        align={"initial": "stretch", "sm": "center"},
        gap="12px",
        padding="12px",
        border="1px solid var(--slate-4)",
        border_radius="14px",
        background_color="white",
    )


@rx.page(route="/my-appointments", title="ตารางนัดหมายของฉัน", on_load=AppState.load_schedule_data)
def my_appointments():
    return member_page(
        "appointments",
        page_header(
            "ตารางนัดหมายของฉัน",
            "การจองคิวและนัดหมายทั้งหมดของคุณ",
            rx.link(rx.button(rx.icon(tag="calendar_plus", size=14), "จองคิวใหม่", color_scheme="purple", radius="full"), href="/booking"),
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(rx.hstack(rx.text("นัดที่จะถึง"), rx.badge(AppState.my_upcoming.length(), radius="full")), value="upcoming"),
                rx.tabs.trigger("ประวัติการนัด", value="past"),
            ),
            rx.tabs.content(
                rx.cond(
                    AppState.my_upcoming.length() > 0,
                    rx.vstack(rx.foreach(AppState.my_upcoming, lambda a: appt_card(a, True)), width="100%", spacing="3"),
                    empty_state("ยังไม่มีนัดหมายที่จะถึง", "calendar"),
                ),
                value="upcoming",
                padding_top="16px",
            ),
            rx.tabs.content(
                rx.cond(
                    AppState.my_past.length() > 0,
                    rx.vstack(rx.foreach(AppState.my_past, lambda a: appt_card(a, False)), width="100%", spacing="3"),
                    empty_state("ยังไม่มีประวัติการนัด", "history"),
                ),
                value="past",
                padding_top="16px",
            ),
            value=AppState.my_appt_tab,
            on_change=AppState.set_my_appt_tab,
            width="100%",
        ),
        slip_dialog(),
    )
