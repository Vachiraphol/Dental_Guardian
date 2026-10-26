"""Small shared building blocks used across pages."""

import reflex as rx


def card(*children: rx.Component, **props) -> rx.Component:
    props.setdefault("padding", ["14px", "18px", "24px"])
    return rx.card(*children, width="100%", class_name="glass-card", **props)


def card_title(text, *extra: rx.Component) -> rx.Component:
    return rx.hstack(
        rx.heading(text, size="4", color="var(--slate-12)"),
        rx.spacer(),
        *extra,
        width="100%",
        align="center",
        margin_bottom="12px",
        wrap="wrap",
    )


def page_header(title, subtitle: str = "", *actions: rx.Component) -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.heading(title, size="7", weight="bold", class_name="gradient-text"),
            *([rx.text(subtitle, color="var(--slate-10)", size="2")] if subtitle else []),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.hstack(*actions, spacing="2", wrap="wrap", align="center"),
        width="100%",
        align="center",
        gap="12px",
        wrap="wrap",
    )


def field(label: str, control: rx.Component, required: bool = False, hint: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, *([rx.text.span(" *", color="var(--red-9)")] if required else []), size="2", weight="medium"),
        control,
        *([rx.text(hint, size="1", color="var(--slate-10)")] if hint else []),
        spacing="1",
        width="100%",
        class_name="dg-field",
    )


def info_row(label: str, value) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", color="var(--slate-10)", min_width="140px"),
        rx.text(rx.cond(value != "", value, "-"), size="2", weight="medium", color="var(--slate-12)"),
        width="100%",
        align="start",
        padding_y="8px",
        border_bottom="1px dashed var(--slate-4)",
    )


def error_callout(message) -> rx.Component:
    return rx.cond(
        message != "",
        rx.callout(message, icon="circle_alert", color_scheme="red", size="1", width="100%"),
    )


def status_badge(status) -> rx.Component:
    return rx.match(
        status,
        ("รออนุมัติ", rx.badge("รออนุมัติ", color_scheme="amber", radius="full")),
        ("ยืนยันแล้ว", rx.badge("ยืนยันแล้ว", color_scheme="blue", radius="full")),
        ("มาตามนัด", rx.badge("มาตามนัด", color_scheme="green", radius="full")),
        ("เลื่อนนัด", rx.badge("เลื่อนนัด", color_scheme="purple", radius="full")),
        ("ยกเลิกนัด", rx.badge("ยกเลิกนัด", color_scheme="gray", radius="full")),
        ("ปฏิเสธ", rx.badge("ปฏิเสธ", color_scheme="red", radius="full")),
        rx.badge(status, radius="full"),
    )


def empty_state(text: str, icon: str = "inbox") -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(tag=icon, size=32, color="var(--slate-8)"),
            rx.text(text, color="var(--slate-10)", size="2", align="center"),
            align="center",
            spacing="2",
        ),
        width="100%",
        padding_y="28px",
    )


def table_wrap(table: rx.Component) -> rx.Component:
    return rx.box(table, width="100%", overflow_x="auto", class_name="dg-table-wrap")


def medical_flags(disease, allergy) -> rx.Component:
    """Highlights congenital disease / drug allergy, which staff must not miss."""
    return rx.hstack(
        rx.cond(disease != "", rx.badge(rx.icon(tag="heart_pulse", size=12), disease, color_scheme="orange", variant="soft")),
        rx.cond(allergy != "", rx.badge(rx.icon(tag="pill", size=12), "แพ้ " + allergy, color_scheme="red", variant="soft")),
        spacing="1",
        wrap="wrap",
    )
