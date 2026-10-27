import reflex as rx


def logo(size: str = "44px") -> rx.Component:
    """The Dental Guardian clinic badge (assets/logo.png)."""
    return rx.image(
        src="/logo.png",
        alt="Dental Guardian Dental Clinic",
        width=size,
        height=size,
        object_fit="contain",
        flex_shrink="0",
    )


def brand(size: str = "44px", subtitle: str = "Dental Clinic") -> rx.Component:
    """Logo + clinic name, used in headers and the staff sidebar."""
    return rx.hstack(
        logo(size),
        rx.vstack(
            rx.text("Dental Guardian", size="4", weight="bold", color="#2F5560", white_space="nowrap", line_height="1.1"),
            rx.text(subtitle, size="1", color="var(--slate-10)", white_space="nowrap", letter_spacing="0.04em"),
            spacing="0",
        ),
        align="center",
        spacing="2",
    )
