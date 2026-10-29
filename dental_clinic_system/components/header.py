import reflex as rx

from dental_clinic_system.components.brand import brand
from dental_clinic_system.state import AppState

PUBLIC_LINKS = [
    ("หน้าแรก", "/"),
    ("จองคิว", "/booking"),
    ("นัดหมายของฉัน", "/my-appointments"),
    ("ประวัติการรักษา", "/my-history"),
]


def nav_link(text: str, href: str, icon: str = "") -> rx.Component:
    return rx.link(
        rx.hstack(
            *([rx.icon(tag=icon, size=16)] if icon else []),
            rx.text(text, size="2", weight="medium"),
            align="center",
            spacing="1",
        ),
        href=href,
        color="var(--slate-12)",
        padding_x="14px",
        padding_y="8px",
        border_radius="999px",
        transition="all 0.2s ease",
        _hover={"background_color": "white", "color": "var(--primary-color)", "box_shadow": "0 2px 8px rgba(0,0,0,0.06)"},
        underline="none",
        white_space="nowrap",
    )


def user_menu() -> rx.Component:
    # ตรวจสอบสิทธิ์ว่าใช่เจ้าหน้าที่ หมอ หรือแอดมินหรือไม่
    is_staff_role = (
        (AppState.user_role == "staff")
        | (AppState.user_role == "dentist")
        | (AppState.user_role == "admin")
    )

    return rx.cond(
        AppState.is_logged_in,
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.avatar(fallback=AppState.user_initials, size="1", radius="full", color_scheme="purple"),
                    rx.text(
                        AppState.user_name,
                        size="2",
                        max_width="140px",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        display=["none", "inline"],
                    ),
                    rx.icon(tag="chevron_down", size=14),
                    variant="soft",
                    color_scheme="purple",
                    radius="full",
                ),
            ),
            rx.menu.content(
                # เมนูสำหรับเจ้าหน้าที่ / ทันตแพทย์ / แอดมิน (คนไข้ทั่วไปจะไม่เห็นเมนูนี้)
                rx.cond(
                    is_staff_role,
                    rx.fragment(
                        rx.menu.item(
                            rx.icon(tag="layout_dashboard", size=14),
                            "แดชบอร์ดผู้ป่วยรายวัน",
                            on_click=rx.redirect("/dashboard"),
                        ),
                        rx.menu.item(
                            rx.icon(tag="calendar", size=14),
                            "จัดการตารางเวลาทันตแพทย์",
                            on_click=rx.redirect("/schedule"),
                        ),
                    ),
                    # เมนูสำหรับคนไข้ทั่วไป
                    rx.fragment(
                        rx.menu.item(
                            rx.icon(tag="user", size=14),
                            "ข้อมูลส่วนตัว",
                            on_click=rx.redirect("/profile"),
                        ),
                        rx.menu.item(
                            rx.icon(tag="pencil", size=14),
                            "แก้ไขข้อมูลส่วนตัว",
                            on_click=rx.redirect("/profile/edit"),
                        ),
                        rx.menu.item(
                            rx.icon(tag="key_round", size=14),
                            "เปลี่ยนรหัสผ่าน",
                            on_click=rx.redirect("/profile/password"),
                        ),
                        rx.menu.item(
                            rx.icon(tag="shield_check", size=14),
                            "ตั้งค่าความเป็นส่วนตัว",
                            on_click=rx.redirect("/profile/privacy"),
                        ),
                    ),
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.icon(tag="log_out", size=14),
                    "ออกจากระบบ",
                    color="red",
                    on_click=AppState.logout,
                ),
            ),
        ),
        # กรณีบุคคลทั่วไปที่ยังไม่ได้เข้าสู่ระบบ
        rx.hstack(
            rx.link(
                rx.button("เข้าสู่ระบบ", variant="soft", color_scheme="purple", radius="full", size="2"),
                href="/login",
            ),
            rx.link(
                rx.button("สมัครสมาชิก", color_scheme="purple", radius="full", size="2"),
                href="/register",
                display=["none", "block"],
            ),
            spacing="2",
        ),
    )

def mobile_menu() -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            rx.icon_button(rx.icon(tag="menu"), variant="ghost", color_scheme="gray", size="3"),
        ),
        rx.menu.content(
            *[rx.menu.item(text, on_click=rx.redirect(href)) for text, href in PUBLIC_LINKS],
            rx.cond(
                (AppState.user_role == "staff")
                | (AppState.user_role == "dentist")
                | (AppState.user_role == "admin"),
                rx.fragment(
                    rx.menu.separator(),
                    rx.menu.item(
                        rx.icon(tag="shield_check", size=14),
                        "สำหรับเจ้าหน้าที่",
                        on_click=rx.redirect("/dashboard"),
                    ),
                ),
                rx.fragment(),
            ),
        ),
    )

def header() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.link(brand(), href="/", underline="none"),
            rx.spacer(),
            rx.hstack(
                rx.hstack(
                    *[nav_link(text, href) for text, href in PUBLIC_LINKS],
                    align="center",
                    spacing="1",
                    padding="4px",
                    border_radius="999px",
                    background_color="rgba(255, 255, 255, 0.65)",
                    border="1px solid rgba(255, 255, 255, 0.9)",
                    box_shadow="0 2px 12px rgba(80, 60, 140, 0.06)",
                    backdrop_filter="blur(8px)",
                ),
                nav_link("สำหรับเจ้าหน้าที่", "/dashboard", "stethoscope"),
                rx.box(width="1px", height="24px", background_color="var(--slate-6)"),
                align="center",
                spacing="3",
                display=["none", "none", "none", "none", "flex"],
            ),
            user_menu(),
            rx.box(mobile_menu(), display=["block", "block", "block", "block", "none"]),
            width="100%",
            max_width="1280px",
            margin="0 auto",
            align="center",
            padding_x=["16px", "24px"],
            padding_y="14px",
            spacing="3",
        ),
        background_color="transparent",
        position="relative",
        z_index="50",
        width="100%",
    )
