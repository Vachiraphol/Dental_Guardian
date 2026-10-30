import reflex as rx
from dental_clinic_system.components.header import header
from dental_clinic_system.components.footer import footer

# รายการบริการ: (ชื่อบริการ, ลิงก์รูปภาพ, ไอคอน)
SERVICES = [
    (
        "ตรวจสุขภาพ & เอกซเรย์",
        "https://images.unsplash.com/photo-1606811841689-23dfddce3e95?auto=format&fit=crop&q=80&w=600",
        "activity",
    ),
    (
        "ขูดหินปูน & ขัดฟัน",
        "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&q=80&w=600",
        "wrench",
    ),
    (
        "อุดฟัน & ถอนฟัน",
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&q=80&w=600",
        "smile",
    ),
]


def service_card(title: str, image_src: str, icon_tag: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            # กล่องรูปภาพ: กำหนดความสูง 200px คงที่ และครอบด้วย object_fit="cover" ให้รูปสเกลเต็มกรอบเท่ากันทุกรูป
            rx.box(
                rx.image(
                    src=image_src,
                    width="100%",
                    height="200px",
                    object_fit="cover",
                    border_top_left_radius="16px",
                    border_top_right_radius="16px",
                ),
                # ไอคอนกลมมุมซ้ายบน
                rx.box(
                    rx.icon(tag=icon_tag, size=16, color="var(--purple-9)"),
                    position="absolute",
                    top="12px",
                    left="12px",
                    background_color="white",
                    border_radius="50%",
                    padding="8px",
                    box_shadow="0 2px 8px rgba(0,0,0,0.12)",
                ),
                position="relative",
                width="100%",
                overflow="hidden",
            ),
            # ส่วนข้อความชื่อบริการด้านล่าง
            rx.center(
                rx.text(
                    title,
                    size="3",
                    weight="bold",
                    color="var(--slate-12)",
                    text_align="center",
                ),
                width="100%",
                padding_y="18px",
                padding_x="12px",
                flex="1",
            ),
            spacing="0",
            height="100%",
        ),
        background_color="white",
        border_radius="18px",
        box_shadow="0 8px 24px rgba(0, 0, 0, 0.05)",
        border="1px solid var(--slate-4)",
        overflow="hidden",
        height="100%",
        width="100%",
        transition="transform 0.2s ease, box-shadow 0.2s ease",
        _hover={
            "transform": "translateY(-4px)",
            "box_shadow": "0 12px 28px rgba(0, 0, 0, 0.08)",
        },
    )


@rx.page(route="/", title="Dental Guardian - หน้าแรก")
def home() -> rx.Component:
    return rx.box(
        # Top Section with light background
        rx.box(
            header(),
            rx.container(
                rx.flex(
                    rx.vstack(
                        rx.heading(
                            rx.text.span("รอยยิ้มสวย", display="inline-block", white_space="nowrap", margin_right="0.3em"),
                            rx.text.span("เริ่มต้นที่นี่", display="inline-block", white_space="nowrap"),
                            size={"initial": "8", "md": "9"},
                            weight="bold",
                            class_name="gradient-text",
                            line_height="1.3",
                            margin_bottom="16px",
                        ),
                        rx.text(
                            "สัมผัสประสบการณ์การดูแลสุขภาพช่องปากระดับโลกกับทีมผู้เชี่ยวชาญของเรา พร้อมเทคโนโลยีที่ทันสมัยเพื่อรอยยิ้มที่สดใสและสุขภาพดีของคุณ",
                            size={"initial": "3", "md": "5"},
                            color="var(--slate-10)",
                            margin_bottom={"initial": "24px", "md": "32px"},
                            line_height="1.8",
                            max_width="500px",
                        ),
                        rx.hstack(
                            rx.box(
                                rx.text("นัดหมายล่วงหน้า", weight="medium", color="white", white_space="nowrap"),
                                background_image="linear-gradient(135deg, #7C69AC 0%, #604a96 100%)",
                                padding_x="32px",
                                padding_y="12px",
                                border_radius="9999px",
                                box_shadow="0 8px 20px -6px rgba(124, 105, 172, 0.6)",
                                transition="all 0.3s ease",
                                _hover={"transform": "translateY(-3px)", "box_shadow": "0 12px 25px -6px rgba(124, 105, 172, 0.8)", "opacity": "0.95"},
                                cursor="pointer",
                                on_click=rx.redirect("/booking"),
                            ),
                            rx.box(
                                rx.text("บริการของเรา", weight="medium", color="var(--primary-color)", white_space="nowrap"),
                                background_color="var(--primary-light)",
                                padding_x="32px",
                                padding_y="12px",
                                border_radius="9999px",
                                transition="all 0.3s ease",
                                _hover={"background_color": "#e4ddef"},
                                cursor="pointer",
                                on_click=rx.redirect("/#services"),
                            ),
                            spacing="3",
                            align="center",
                            wrap="wrap",
                        ),
                        align="start",
                        justify="center",
                        height="100%",
                        padding_right={"initial": "0", "md": "32px"},
                        class_name="animate-fade-in",
                        flex="1",
                    ),
                    rx.box(
                        rx.image(
                            src="https://images.unsplash.com/photo-1606811841689-23dfddce3e95?auto=format&fit=crop&q=80&w=800",
                            border_radius="32px",
                            box_shadow="0 25px 50px -12px rgba(0,0,0,0.15)",
                            height={"initial": "240px", "md": "400px"},
                            width="100%",
                            object_fit="cover",
                            class_name="animate-float",
                        ),
                        width="100%",
                        display="block",
                        class_name="animate-slide-in",
                        flex="1",
                    ),
                    direction={"initial": "column", "md": "row"},
                    gap={"initial": "32px", "md": "48px"},
                    padding_y={"initial": "16px", "md": "32px"},
                    padding_x={"initial": "4px", "md": "0"},
                    align="center",
                    position="relative",
                    z_index="10",
                ),
                rx.box(
                    position="absolute",
                    top="-5%",
                    left="-10%",
                    width="300px",
                    height="300px",
                    background_color="#D8B4FE",
                    opacity="0.3",
                    filter="blur(60px)",
                    border_radius="50%",
                    class_name="animate-float",
                    z_index="0",
                ),
                rx.box(
                    position="absolute",
                    bottom="10%",
                    right="-5%",
                    width="250px",
                    height="250px",
                    background_color="#93C5FD",
                    opacity="0.3",
                    filter="blur(60px)",
                    border_radius="50%",
                    class_name="animate-float",
                    animation_delay="2s",
                    z_index="0",
                ),
                position="relative",
                overflow="hidden",
            ),
            class_name="gradient-bg-animated",
            padding_bottom="16px",
            border_bottom_left_radius="40px",
            border_bottom_right_radius="40px",
            box_shadow="sm",
            margin_bottom="16px",
        ),
        # Services Section
        rx.container(
            rx.center(
                rx.vstack(
                    rx.heading(
                        "บริการทางทันตกรรมของเรา",
                        size={"initial": "6", "md": "8"},
                        weight="bold",
                        color="var(--slate-12)",
                        margin_bottom={"initial": "24px", "md": "48px"},
                        text_align="center",
                        class_name="animate-fade-in-delayed",
                    ),
                    rx.grid(
                        *[service_card(title, img, icon) for title, img, icon in SERVICES],
                        columns={"initial": "1", "sm": "2", "md": "3"},
                        spacing="4",
                        width="100%",
                        align_items="stretch",
                    ),
                    width="100%",
                    padding_y="40px",
                ),
                width="100%",
            ),
            id="services",
            max_width="1150px",
            margin="0 auto",
            padding_x=["12px", "16px"],
        ),
        footer(),
        background_color="white",
        min_height="100vh",
    )