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


def brand(
    size: str = "76px",
    subtitle: str = "Dental Clinic",
    title_size: str = "7",
    subtitle_size: str = "3",
) -> rx.Component:
    """Logo + clinic name, used in headers and the staff sidebar."""
    is_compact = size in ["34px", "36px", "40px", "42px", "46px", "48px", "52px", "56px"]

    return rx.hstack(
        logo(size),
        rx.vstack(
            rx.text(
                "Dental Guardian",
                font_size="1.25rem" if is_compact else "1.65rem",  # ขยายขนาดตัวหนังสือ Dental Guardian ให้ใหญ่เด่นชัด
                weight="bold",
                font_weight="900",
                color="#1e3f4b",
                white_space="nowrap",
                line_height="1.1",
                letter_spacing="-0.02em",
            ),
            rx.text(
                subtitle,
                font_size="0.95rem" if is_compact else "1.05rem",  # ขยายขนาดคำบรรยายด้านล่างให้อ่านง่ายขึ้น
                weight="bold",
                color="var(--slate-10)",
                white_space="nowrap",
                letter_spacing="0.02em",
                line_height="1.1",
            ),
            spacing="1",
            align_items="start",
            justify="center",
        ),
        align="center",
        spacing="3",
    )