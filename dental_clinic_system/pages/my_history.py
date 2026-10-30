"""SRS 5.4 (ลูกค้า) หน้าประวัติการรักษา."""

import reflex as rx

from dental_clinic_system.components.dental_chart import dental_chart
from dental_clinic_system.components.history import chart_badge, entry_item
from dental_clinic_system.components.layout import member_page
from dental_clinic_system.components.ui import card, card_title, empty_state, page_header
from dental_clinic_system.state import AppState


@rx.page(route="/my-history", title="ประวัติการรักษา - Dental Guardian", on_load=AppState.load_schedule_data)
def my_history() -> rx.Component:
    return member_page(
        "history",
        page_header("ประวัติการรักษา", "แตะที่ซี่ฟันเพื่อดูว่าเคยรักษาอะไร เมื่อไร", chart_badge()),
        card(
            dental_chart(AppState.my_treated_teeth, AppState.my_selected_tooth, AppState.select_my_tooth),
        ),
        card(
            rx.cond(
                AppState.my_selected_tooth != "",
                rx.vstack(
                    card_title(AppState.my_selected_tooth_label,
                               rx.button("ดูทั้งหมด", size="1", variant="ghost", on_click=AppState.select_my_tooth(""))),
                    rx.cond(
                        AppState.my_tooth_entries.length() > 0,
                        rx.vstack(rx.foreach(AppState.my_tooth_entries, lambda e: entry_item(e, False)), width="100%", spacing="2"),
                        empty_state("ฟันซี่นี้ยังไม่มีประวัติการรักษา", "smile"),
                    ),
                    width="100%",
                ),
                rx.vstack(
                    card_title("ประวัติการรักษาทั้งหมด", rx.badge(AppState.my_entries.length().to_string() + " รายการ", variant="soft")),
                    rx.cond(
                        AppState.my_entries.length() > 0,
                        rx.vstack(rx.foreach(AppState.my_entries, lambda e: entry_item(e)), width="100%", spacing="2"),
                        empty_state("ยังไม่มีประวัติการรักษา", "clipboard"),
                    ),
                    width="100%",
                ),
            ),
        ),
    )
