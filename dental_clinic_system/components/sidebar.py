import reflex as rx

from dental_clinic_system.components.brand import brand, logo
from dental_clinic_system.state import AppState

# Staff pages from SRS-3 5.3 and 5.4
MENU = [
    ("นัดหมายและจองคิว", [
        ("dashboard", "แดชบอร์ดผู้ป่วยรายวัน", "layout_dashboard", "/dashboard"),
        ("requests", "จัดการคำขอจองคิว", "inbox", "/requests"),
        ("appointments", "จัดการนัดหมายคนไข้", "calendar_check", "/appointments"),
        ("schedule", "ตั้งค่าตารางเวลาทันตแพทย์", "calendar_cog", "/schedule"),
    ]),
    ("ประวัติการรักษา", [
        ("records", "บันทึกการรักษาและผังฟัน", "clipboard_pen", "/records"),
        ("summary", "สรุปประวัติเวชระเบียนรวม", "file_text", "/records/summary"),
    ]),
]


def sidebar_item(key: str, text: str, icon: str, url: str, active: str) -> rx.Component:
    is_active = key == active
    return rx.link(
        rx.hstack(
            rx.icon(tag=icon, size=18, color="var(--primary-color)" if is_active else "var(--slate-10)"),
            rx.text(text, size="2", weight="bold" if is_active else "medium",
                    color="var(--primary-color)" if is_active else "var(--slate-11)"),
            rx.spacer(),
            rx.cond(
                AppState.pending_count > 0,
                rx.badge(AppState.pending_count, color_scheme="red", radius="full", variant="solid"),
            ) if key == "requests" else rx.fragment(),
            spacing="3",
            align="center",
            padding_x="14px",
            padding_y="10px",
            border_radius="10px",
            background_color="var(--primary-light)" if is_active else "transparent",
            transition="all 0.2s ease-in-out",
            _hover={"background_color": "var(--purple-3)"},
            width="100%",
        ),
        href=url,
        underline="none",
        width="100%",
    )


def sidebar(active: str = "") -> rx.Component:
    sections = []
    for title, items in MENU:
        sections.append(rx.text(title, size="1", weight="bold", color="var(--slate-9)", padding_x="14px", padding_top="12px"))
        sections.extend(sidebar_item(*item, active) for item in items)
    return rx.box(
        rx.vstack(
            rx.link(
                brand("42px", "สำหรับหมอฟันและพยาบาล"),
                href="/",
                underline="none",
                padding_x="12px",
                padding_bottom="16px",
                border_bottom="1px solid var(--slate-4)",
                width="100%",
            ),
            *sections,
            rx.spacer(),
            rx.vstack(
                rx.hstack(
                    rx.avatar(fallback=AppState.user_initials, size="2", radius="full", color_scheme="purple"),
                    rx.vstack(
                        rx.text(AppState.user_name, size="2", weight="medium"),
                        rx.text("เจ้าหน้าที่คลินิก", size="1", color="var(--slate-10)"),
                        spacing="0",
                    ),
                    align="center",
                    padding_x="12px",
                    width="100%",
                ),
                rx.button(rx.icon(tag="log_out", size=16), "ออกจากระบบ", on_click=AppState.logout,
                          variant="soft", color_scheme="gray", width="100%"),
                border_top="1px solid var(--slate-4)",
                padding_top="16px",
                width="100%",
                spacing="3",
            ),
            width="100%",
            height="100%",
            align="start",
            spacing="1",
        ),
        width="280px",
        min_width="280px",
        height="100vh",
        position="sticky",
        top="0",
        display=["none", "none", "block"],
        background_color="white",
        box_shadow="4px 0px 24px rgba(0, 0, 0, 0.04)",
        padding_y="20px",
        padding_x="12px",
        overflow_y="auto",
    )


def mobile_topbar(active: str = "") -> rx.Component:
    """Compact staff navigation for phones: logo + current page + dropdown menu."""
    current = next((text for _, items in MENU for key, text, _, _ in items if key == active), "")
    menu_items = []
    for title, items in MENU:
        menu_items.append(rx.text(title, size="1", weight="bold", color="var(--slate-9)", padding_x="8px", padding_y="4px"))
        menu_items.extend(
            rx.menu.item(
                rx.icon(tag=icon, size=14), text,
                rx.cond(AppState.pending_count > 0, rx.badge(AppState.pending_count, color_scheme="red", radius="full"))
                if key == "requests" else rx.fragment(),
                on_click=rx.redirect(url),
                **({"color": "var(--primary-color)"} if key == active else {}),
            )
            for key, text, icon, url in items
        )
        menu_items.append(rx.menu.separator())
    return rx.hstack(
        rx.link(logo("36px"), href="/"),
        rx.vstack(
            rx.text("Dental Guardian", size="1", color="var(--slate-10)"),
            rx.text(current, size="2", weight="bold", white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            spacing="0",
            min_width="0",
            flex="1",
        ),
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.icon(tag="menu", size=18),
                    rx.cond(AppState.pending_count > 0, rx.badge(AppState.pending_count, color_scheme="red", radius="full", variant="solid")),
                    variant="soft",
                    color_scheme="purple",
                ),
            ),
            rx.menu.content(
                *menu_items,
                rx.menu.item(rx.icon(tag="log_out", size=14), "ออกจากระบบ (" + AppState.user_name + ")", color="red", on_click=AppState.logout),
                align="end",
            ),
        ),
        width="100%",
        align="center",
        padding_x="16px",
        padding_y="10px",
        background_color="white",
        box_shadow="0 2px 12px rgba(0, 0, 0, 0.06)",
        position="sticky",
        top="0",
        z_index="40",
        display=["flex", "flex", "none"],
    )
