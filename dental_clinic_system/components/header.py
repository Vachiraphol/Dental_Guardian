import reflex as rx

from dental_clinic_system.components.brand import brand
from dental_clinic_system.state import AppState


def nav_link(text: str, href, icon: str = "", text_size: str = "3", icon_size: int = 18) -> rx.Component:
    return rx.link(
        rx.hstack(
            *([rx.icon(tag=icon, size=icon_size)] if icon else []),
            rx.text(text, size=text_size, weight="medium"),
            align="center",
            spacing="2",
        ),
        href=href,
        color="var(--slate-12)",
        padding_x="16px",
        padding_y="8px",
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
    is_staff_or_admin = (AppState.user_role == "staff") | (AppState.user_role == "admin")
    is_dentist = AppState.user_role == "dentist"

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
                    size="2",
                    padding_x="12px",
                    padding_y="6px",
                    height="36px",
                ),
            ),
            rx.menu.content(
                rx.cond(
                    is_dentist,
                    rx.fragment(
                        rx.menu.item(
                            rx.icon(tag="file_pen_line", size=15),
                            "บันทึกการรักษาและผังฟัน",
                            on_click=rx.redirect("/records"),
                        ),
                        rx.menu.item(
                            rx.icon(tag="calendar", size=15),
                            "ตารางเวลาปฏิบัติงานทันตแพทย์",
                            on_click=rx.redirect("/schedule"),
                        ),
                    ),
                    rx.cond(
                        is_staff_or_admin,
                        rx.fragment(
                            rx.menu.item(
                                rx.icon(tag="layout_dashboard", size=15),
                                "แดชบอร์ดผู้ป่วยรายวัน",
                                on_click=rx.redirect("/dashboard"),
                            ),
                            rx.menu.item(
                                rx.hstack(
                                    rx.hstack(
                                        rx.icon(tag="inbox", size=15),
                                        rx.text("จัดการคำขอจองคิว"),
                                        align="center",
                                        spacing="2",
                                    ),
                                    rx.spacer(),
                                    rx.cond(
                                        AppState.pending_count > 0,
                                        rx.badge(
                                            AppState.pending_count,
                                            color_scheme="red",
                                            variant="solid",
                                            radius="full",
                                            size="1",
                                        ),
                                    ),
                                    width="100%",
                                    align="center",
                                ),
                                on_click=rx.redirect("/requests"),
                            ),
                            rx.menu.item(
                                rx.icon(tag="calendar_check", size=15),
                                "จัดการนัดหมายคนไข้",
                                on_click=rx.redirect("/appointments"),
                            ),
                            rx.menu.item(
                                rx.icon(tag="calendar", size=15),
                                "ตารางเวลาปฏิบัติงานทันตแพทย์",
                                on_click=rx.redirect("/schedule"),
                            ),
                            rx.menu.separator(),
                            rx.menu.item(
                                rx.icon(tag="file_pen_line", size=15),
                                "บันทึกการรักษาและผังฟัน",
                                on_click=rx.redirect("/records"),
                            ),
                            rx.menu.item(
                                rx.icon(tag="file_text", size=15),
                                "สรุปประวัติเวชระเบียนรวม",
                                on_click=rx.redirect("/records/summary"),
                            ),
                        ),
                        rx.fragment(
                            rx.menu.item(
                                rx.icon(tag="user", size=15),
                                "ข้อมูลส่วนตัว",
                                on_click=rx.redirect("/profile"),
                            ),
                            rx.menu.item(
                                rx.icon(tag="pencil", size=15),
                                "แก้ไขข้อมูลส่วนตัว",
                                on_click=rx.redirect("/profile/edit"),
                            ),
                            rx.menu.item(
                                rx.icon(tag="key_round", size=15),
                                "เปลี่ยนรหัสผ่าน",
                                on_click=rx.redirect("/profile/password"),
                            ),
                            rx.menu.item(
                                rx.icon(tag="shield_check", size=15),
                                "ตั้งค่าความเป็นส่วนตัว",
                                on_click=rx.redirect("/profile/privacy"),
                            ),
                        ),
                    ),
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.icon(tag="log_out", size=15),
                    "ออกจากระบบ",
                    color="red",
                    on_click=AppState.logout,
                ),
            ),
        ),
        # บุคคลทั่วไป (ยังไม่ได้ล็อกอิน)
        rx.hstack(
            rx.link(
                rx.button(
                    "เข้าสู่ระบบ",
                    variant="soft",
                    color_scheme="purple",
                    radius="full",
                    size={"initial": "2", "md": "3"},
                    padding_x={"initial": "10px", "md": "16px"},
                ),
                href="/login",
            ),
            rx.link(
                rx.button(
                    "สมัครสมาชิก",
                    color_scheme="purple",
                    radius="full",
                    size={"initial": "2", "md": "3"},
                    padding_x={"initial": "14px", "md": "18px"},
                ),
                href="/register",
                display=["none", "block"],
            ),
            spacing="2",
            align="center",
            flex_shrink="0",
        ),
    )


def mobile_menu() -> rx.Component:
    is_staff_or_admin = (AppState.user_role == "staff") | (AppState.user_role == "admin")
    is_dentist = AppState.user_role == "dentist"

    return rx.menu.root(
        rx.menu.trigger(
            rx.icon_button(rx.icon(tag="menu", size=22), variant="ghost", color_scheme="gray", size="3"),
        ),
        rx.menu.content(
            rx.menu.item("หน้าแรก", on_click=rx.redirect("/")),
            rx.menu.item("จองคิว", on_click=rx.redirect("/booking")),
            rx.menu.item(
                "นัดหมายของฉัน",
                on_click=rx.redirect(rx.cond(AppState.is_logged_in, "/my-appointments", "/login")),
            ),
            rx.menu.item(
                "ประวัติการรักษา",
                on_click=rx.redirect(rx.cond(AppState.is_logged_in, "/my-history", "/login")),
            ),
            rx.cond(
                is_dentist,
                rx.fragment(
                    rx.menu.separator(),
                    rx.menu.item("บันทึกการรักษาและผังฟัน", on_click=rx.redirect("/records")),
                    rx.menu.item("ตารางเวลาปฏิบัติงานทันตแพทย์", on_click=rx.redirect("/schedule")),
                ),
                rx.cond(
                    is_staff_or_admin,
                    rx.fragment(
                        rx.menu.separator(),
                        rx.menu.item("แดชบอร์ดผู้ป่วยรายวัน", on_click=rx.redirect("/dashboard")),
                        rx.menu.item(
                            rx.hstack(
                                rx.text("จัดการคำขอจองคิว"),
                                rx.spacer(),
                                rx.cond(
                                    AppState.pending_count > 0,
                                    rx.badge(
                                        AppState.pending_count,
                                        color_scheme="red",
                                        variant="solid",
                                        radius="full",
                                        size="1",
                                    ),
                                ),
                                width="100%",
                                align="center",
                            ),
                            on_click=rx.redirect("/requests"),
                        ),
                        rx.menu.item("จัดการนัดหมายคนไข้", on_click=rx.redirect("/appointments")),
                        rx.menu.item("ตารางเวลาปฏิบัติงานทันตแพทย์", on_click=rx.redirect("/schedule")),
                        rx.menu.item("บันทึกการรักษาและผังฟัน", on_click=rx.redirect("/records")),
                        rx.menu.item("สรุปประวัติเวชระเบียนรวม", on_click=rx.redirect("/records/summary")),
                    ),
                    rx.fragment(),
                ),
            ),
        ),
    )


def header() -> rx.Component:
    return rx.box(
        rx.hstack(
            # 1. ฝั่งซ้าย: แบรนด์และโลโก้ (อนุญาตให้ย่อขนาดตามหน้าจอมือถือได้)
            rx.link(brand(), href="/", underline="none", flex_shrink="1", min_width="0"),

            rx.spacer(),

            # 2. ตรงกลาง: แคปซูลเมนูนำทางหลัก (แสดงเฉพาะจอ Desktop >= 1280px)
            rx.hstack(
                nav_link("หน้าแรก", "/"),
                nav_link("จองคิว", "/booking"),
                nav_link(
                    "นัดหมายของฉัน",
                    rx.cond(AppState.is_logged_in, "/my-appointments", "/login"),
                ),
                nav_link(
                    "ประวัติการรักษา",
                    rx.cond(AppState.is_logged_in, "/my-history", "/login"),
                ),
                align="center",
                spacing="1",
                padding="6px 8px",
                border_radius="999px",
                background_color="rgba(255, 255, 255, 0.85)",
                border="1px solid rgba(255, 255, 255, 0.95)",
                box_shadow="0 4px 18px rgba(80, 60, 140, 0.08)",
                backdrop_filter="blur(12px)",
                display=["none", "none", "none", "none", "flex"],
                flex_shrink="0",
            ),

            rx.spacer(display=["none", "none", "none", "none", "block"]),

            # 3. ฝั่งขวา: ปุ่มเข้าสู่ระบบ / สมัครสมาชิก และปุ่มเมนูสำหรับมือถือ & iPad (< 1280px)
            rx.hstack(
                user_menu(),
                rx.box(mobile_menu(), display=["block", "block", "block", "block", "none"]),
                align="center",
                spacing="1",
                flex_shrink="0",
            ),
            width="100%",
            max_width="1280px",
            margin="0 auto",
            align="center",
            padding_x=["10px", "20px", "24px"],
            padding_y="10px",
            gap=["6px", "12px"],
        ),
        background_color="transparent",
        position="relative",
        z_index="50",
        width="100%",
    )