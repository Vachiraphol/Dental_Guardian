"""Page shells: public pages, member (customer) pages and staff pages."""

import reflex as rx

from dental_clinic_system.components.footer import footer
from dental_clinic_system.components.header import header
from dental_clinic_system.components.sidebar import mobile_topbar, sidebar
from dental_clinic_system.state import AppState

MEMBER_MENU = [
    ("profile", "ข้อมูลส่วนตัว", "user", "/profile"),
    ("edit", "แก้ไขข้อมูลส่วนตัว", "pencil", "/profile/edit"),
    ("password", "เปลี่ยนรหัสผ่าน", "key_round", "/profile/password"),
    ("privacy", "ตั้งค่าความเป็นส่วนตัว", "shield_check", "/profile/privacy"),
    ("appointments", "ตารางนัดหมายของฉัน", "calendar_days", "/my-appointments"),
    ("history", "ประวัติการรักษา", "clipboard_list", "/my-history"),
]


def login_required(message: str, href: str = "/login", button: str = "เข้าสู่ระบบ") -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.icon(tag="lock", size=36, color="var(--primary-color)"),
                rx.heading("กรุณาเข้าสู่ระบบ", size="5"),
                rx.text(message, color="var(--slate-10)", align="center"),
                rx.link(rx.button(button, color_scheme="purple", radius="full", size="3"), href=href),
                align="center",
                spacing="3",
            ),
            padding="40px",
            max_width="440px",
            width="100%",
        ),
        width="100%",
        padding_y="64px",
        padding_x="16px",
    )


def public_page(*children: rx.Component, hero_title: str = "", hero_text: str = "") -> rx.Component:
    """Header + optional gradient hero + centered content + footer."""
    top = [header()]
    if hero_title:
        top.append(
            rx.vstack(
                rx.heading(hero_title, size={"initial": "7", "md": "8"}, class_name="gradient-text", text_align="center"),
                *([rx.text(hero_text, color="var(--slate-10)", size="3", text_align="center")] if hero_text else []),
                align="center",
                padding_top="8px",
                padding_bottom="28px",
                padding_x="16px",
            )
        )
    return rx.box(
        rx.box(*top, class_name="gradient-bg-animated", border_bottom_left_radius=["24px", "40px"], border_bottom_right_radius=["24px", "40px"]),
        rx.box(*children, max_width="1150px", margin="0 auto", padding_x=["12px", "16px"], padding_y=["20px", "32px"], width="100%"),
        footer(),
        background_color="white",
        min_height="100vh",
    )


def member_menu(active: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.avatar(fallback=AppState.user_initials, size="4", radius="full", color_scheme="purple"),
                rx.vstack(
                    rx.text(AppState.user_name, weight="bold"),
                    rx.badge(AppState.current_patient_id, color_scheme="gray"),
                    spacing="1",
                ),
                align="center",
                padding_bottom="12px",
                border_bottom="1px solid var(--slate-4)",
                width="100%",
            ),
            *[
                rx.link(
                    rx.hstack(
                        rx.icon(tag=icon, size=16),
                        rx.text(text, size="2", weight="bold" if key == active else "medium"),
                        align="center",
                        padding_x="12px",
                        padding_y="8px",
                        border_radius="8px",
                        width="100%",
                        color="var(--primary-color)" if key == active else "var(--slate-11)",
                        background_color="var(--primary-light)" if key == active else "transparent",
                        _hover={"background_color": "var(--purple-3)"},
                    ),
                    href=href,
                    underline="none",
                    width="100%",
                )
                for key, text, icon, href in MEMBER_MENU
            ],
            rx.button(rx.icon(tag="log_out", size=14), "ออกจากระบบ", variant="ghost", color_scheme="red",
                      on_click=AppState.logout, width="100%", margin_top="8px"),
            spacing="1",
            width="100%",
        ),
        padding="16px",
        width="100%",
    )


def member_tabs(active: str) -> rx.Component:
    """Horizontal, swipeable member menu for phones."""
    return rx.hstack(
        *[
            rx.link(
                rx.hstack(
                    rx.icon(tag=icon, size=14),
                    rx.text(text, size="2", white_space="nowrap"),
                    align="center",
                    spacing="1",
                    padding_x="12px",
                    padding_y="8px",
                    border_radius="999px",
                    color="white" if key == active else "var(--slate-11)",
                    background_color="var(--primary-color)" if key == active else "white",
                    border="1px solid var(--slate-5)",
                ),
                href=href,
                underline="none",
                flex_shrink="0",
            )
            for key, text, icon, href in MEMBER_MENU
        ],
        spacing="2",
        width="100%",
        overflow_x="auto",
        padding_bottom="4px",
        class_name="dg-scroll-x",
        display=["flex", "flex", "none"],
    )


def member_page(active: str, *children: rx.Component) -> rx.Component:
    """Customer account pages (SRS 5.2–5.4): side menu + content.

    TODO(backend): only logged-in patients may see these pages — wrap the content in
    rx.cond(AppState.is_patient, ..., login_required(...)) once login works.
    """
    return public_page(
        rx.flex(
            rx.box(member_menu(active), width="260px", flex_shrink="0", display=["none", "none", "block"]),
            member_tabs(active),
            rx.vstack(*children, width="100%", spacing="4", min_width="0"),
            flex_direction=["column", "column", "row"],
            gap="24px",
            align="start",
            width="100%",
        ),
    )


def staff_page(active: str, *children: rx.Component) -> rx.Component:
    """Staff pages (dentist / nurse): sidebar + content.

    TODO(backend): only logged-in staff may see these pages — wrap in
    rx.cond(AppState.is_staff, ..., public_page(login_required(...))) once login works.
    """
    return rx.flex(
        sidebar(active),
        mobile_topbar(active),
        rx.box(
            rx.vstack(
                *children,
                width="100%",
                max_width="1200px",
                margin_x="auto",
                spacing="4",
                padding=["12px", "16px", "24px", "32px"],
            ),
            width="100%",
            min_width="0",
            min_height="100vh",
            background_color="var(--slate-2)",
            overflow_x="hidden",
        ),
        width="100%",
        background_color="var(--slate-2)",
        flex_direction=["column", "column", "row"],
    )
