import reflex as rx

from dental_clinic_system.components.brand import brand
from dental_clinic_system.state import AppState

PUBLIC_LINKS = [
    ("หน้าแรก", "/"),
    ("จองคิว", "/booking"),
    ("นัดหมายของฉัน", "/my-appointments"),
    ("ประวัติการรักษา", "/my-history"),
]


def nav_link(text: str, href: str, icon: str = "", text_size: str = "3", icon_size: int = 18) -> rx.Component:
    return rx.link(
        rx.hstack(
            *([rx.icon(tag=icon, size=icon_size)] if icon else []),
            rx.text(text, size=text_size, weight="bold" if text_size == "3" else "medium"),
            align="center",
            spacing="1",
        ),
        href=href,
        color="var(--slate-12)",
        padding_x="12px" if text_size == "2" else "18px",
        padding_y="6px" if text_size == "2" else "10px",
        border_radius="999px",
        transition="all 0.2s ease",
        _hover={
            "background_color": "white",
            "color": "var(--primary-color)",
            "box_shadow": "0 2px 10px rgba(0,0,0,0.08)",
        },
        underline="none",
        white_space="nowrap",
    )


def user_menu() -> rx.Component:
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
                        weight="medium",
                        max_width="130px",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        display=["none", "inline"],
                    ),
                    rx.icon(tag="chevron_down", size=14),
                    variant="soft",
                    color_scheme="purple",
                    radius="full",
                    size="2",              # ลดจาก size="3" เป็น size="2" ให้ขนาดพอดี
                    padding_x="10px",       # ลดระยะขอบซ้ายขวาให้กระชับ
                    padding_y="6px",
                    height="36px",         # ล็อกความสูงให้พอดีกับแถบเมนู
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
                            "ตารางเวลาปฏิบัติงานทันตแพทย์",
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
                rx.button("เข้าสู่ระบบ", variant="soft", color_scheme="purple", radius="full", size="3"),
                href="/login",
            ),
            rx.link(
                rx.button("สมัครสมาชิก", color_scheme="purple", radius="full", size="3"),
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
            # 1. ฝั่งซ้าย: โลโก้
            rx.link(brand(), href="/", underline="none", flex_shrink="0"),
            
            # 2. ตรงกลาง: แคปซูลเมนูนำทางหลัก (ปรับ padding ให้นิ่ง ไม่กว้างจนล้นไปทับฝั่งขวา)
            rx.box(
                rx.hstack(
                    *[nav_link(text, href) for text, href in PUBLIC_LINKS],
                    align="center",
                    spacing="1",
                    padding="4px 6px",     # ปรับลด padding ให้แคปซูลกระชับขึ้น
                    border_radius="999px",
                    background_color="rgba(255, 255, 255, 0.8)",
                    border="1px solid rgba(255, 255, 255, 0.95)",
                    box_shadow="0 4px 16px rgba(80, 60, 140, 0.08)",
                    backdrop_filter="blur(10px)",
                ),
                position="absolute",
                left="50%",
                transform="translateX(-50%)",
                display=["none", "none", "none", "none", "block"],
                z_index="10",
            ),

            rx.spacer(),

            # 3. ฝั่งขวา: เมนูสำหรับเจ้าหน้าที่ + โปรไฟล์
            rx.hstack(
                nav_link("สำหรับเจ้าหน้าที่", "/dashboard", "stethoscope", text_size="2", icon_size=15),
                rx.box(width="1px", height="20px", background_color="var(--slate-6)"),
                user_menu(),
                rx.box(mobile_menu(), display=["block", "block", "block", "block", "none"]),
                align="center",
                spacing="2",
                flex_shrink="0",
                z_index="20",
            ),
            width="100%",
            max_width="1280px",
            margin="0 auto",
            align="center",
            padding_x=["16px", "24px"],
            padding_y="12px",
            position="relative",
        ),
        background_color="transparent",
        position="relative",
        z_index="50",
        width="100%",
    )