import reflex as rx


def logo(size: str = "76px") -> rx.Component:
    """The Dental Guardian clinic badge (/logo.png)."""
    return rx.image(
        src="/logo.png",
        alt="Dental Guardian Dental Clinic",
        width="auto",
        height=size,
        object_fit="contain",
        flex_shrink="0",
        margin_right="-4px",
    )


def brand(size: str = "76px", subtitle: str = "Dental Clinic") -> rx.Component:
    """Logo + clinic name, used in headers and the staff sidebar."""
    return rx.hstack(
        logo(size),
        rx.vstack(
            rx.text(
                "Dental Guardian",
                size="7",  # ขยายขนาดตัวอักษรใหญ่ขึ้นเป็น size="7"
                weight="bold",
                font_weight="900",  # ปรับความหนาระดับสูงสุด (Black font) ให้เด่นชัด
                color="#1e3f4b",  # โทนสีเข้มคมขึ้น
                white_space="nowrap",
                line_height="1",
                letter_spacing="-0.03em",
            ),
            rx.text(
                subtitle,
                size="3",  # ขยายคำบรรยายด้านล่างเป็น size="3"
                weight="bold",
                color="var(--slate-10)",
                white_space="nowrap",
                letter_spacing="0.12em",
                text_transform="uppercase",
                line_height="1",
            ),
            spacing="1",
            align_items="start",
            justify="center",
        ),
        align="center",
        spacing="2",
    )