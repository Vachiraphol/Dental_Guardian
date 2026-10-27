import reflex as rx

from dental_clinic_system.components.brand import brand

def footer() -> rx.Component:
    return rx.box(
        rx.container(
            rx.grid(
                rx.vstack(
                    brand("52px"),
                    rx.text("มอบการดูแลรักษาสุขภาพช่องปากที่ดีที่สุดสำหรับครอบครัวคุณ", size="2", color="var(--slate-10)"),
                    align="start",
                    spacing="3",
                ),
                rx.vstack(
                    rx.heading("ติดต่อเรา", size="4", color="var(--slate-12)"),
                    rx.text("📞 +66 2 123 4567", size="2", color="var(--slate-10)"),
                    rx.text("📧 contact@dentalguardian.com", size="2", color="var(--slate-10)"),
                    align="start",
                    spacing="2",
                ),
                rx.vstack(
                    rx.heading("สถานที่ตั้ง", size="4", color="var(--slate-12)"),
                    rx.text("123 Health Ave,", size="2", color="var(--slate-10)"),
                    rx.text("Bangkok, 10110", size="2", color="var(--slate-10)"),
                    align="start",
                    spacing="2",
                ),
                columns={"initial": "1", "sm": "2", "md": "3"},
                spacing={"initial": "6", "md": "9"},
                width="100%",
            ),
            rx.box(
                rx.text("© 2026 Dental Guardian. All rights reserved.", size="2", color="var(--slate-9)", align="center"),
                margin_top="32px",
                padding_top="20px",
                border_top="1px solid var(--slate-5)",
                width="100%",
            ),
            padding_top={"initial": "32px", "md": "48px"},
            padding_bottom="24px",
            padding_x="16px",
        ),
        background_color="var(--footer-bg)",
        border_top_left_radius={"initial": "24px", "md": "40px"},
        border_top_right_radius={"initial": "24px", "md": "40px"},
        width="100%",
        margin_top="48px",
    )
