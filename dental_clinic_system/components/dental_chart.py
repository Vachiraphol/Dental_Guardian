"""Interactive dental chart of the 32 permanent teeth, numbered 1–32 — SRS 5.4."""

import reflex as rx

from dental_clinic_system.state import (
    MOLARS, PERMANENT_LOWER, PERMANENT_UPPER, tooth_label,
)


def _tooth(t: str, treated, selected, on_select, upper: bool) -> rx.Component:
    molar = t in MOLARS
    is_selected = selected == t
    is_treated = treated.contains(t)
    return rx.tooltip(
        rx.vstack(
            *([rx.text(t, size="1", color="var(--slate-10)")] if not upper else []),
            rx.box(
                rx.cond(is_treated, rx.box(width="6px", height="6px", border_radius="50%", background_color=rx.cond(is_selected, "white", "var(--orange-9)"))),
                width="100%",
                height="34px" if molar else "28px",
                display="flex",
                align_items="center",
                justify_content="center",
                border_radius="8px 8px 14px 14px" if upper else "14px 14px 8px 8px",
                border=rx.cond(is_selected, "2px solid var(--purple-10)",
                               rx.cond(is_treated, "2px solid var(--orange-8)", "1.5px solid var(--slate-6)")),
                background_color=rx.cond(is_selected, "var(--purple-9)",
                                         rx.cond(is_treated, "var(--orange-3)", "#ffffff")),
                transition="all 0.15s ease",
                _hover={"transform": "scale(1.08)", "border_color": "var(--purple-8)"},
            ),
            *([rx.text(t, size="1", color="var(--slate-10)")] if upper else []),
            spacing="1",
            align="center",
            flex="1",
            min_width="0",
            max_width="46px",
            cursor="pointer",
            on_click=on_select(t),
        ),
        content=tooth_label(t),
    )


def _row(teeth: list[str], treated, selected, on_select, upper: bool) -> rx.Component:
    half = len(teeth) // 2
    return rx.hstack(
        rx.hstack(*[_tooth(t, treated, selected, on_select, upper) for t in teeth[:half]], spacing="1", flex="1", justify="end"),
        rx.box(width="2px", height="44px", background_color="var(--slate-6)", flex_shrink="0"),
        rx.hstack(*[_tooth(t, treated, selected, on_select, upper) for t in teeth[half:]], spacing="1", flex="1", justify="start"),
        width="100%",
        spacing="2",
        align="end" if upper else "start",
    )


def _arch(upper_teeth: list[str], lower_teeth: list[str], treated, selected, on_select) -> rx.Component:
    return rx.vstack(
        rx.hstack(rx.text("ขวาของผู้ป่วย", size="1", color="var(--slate-9)"), rx.spacer(),
                  rx.text("ขากรรไกรบน", size="1", weight="bold", color="var(--slate-10)"), rx.spacer(),
                  rx.text("ซ้ายของผู้ป่วย", size="1", color="var(--slate-9)"), width="100%"),
        _row(upper_teeth, treated, selected, on_select, True),
        rx.divider(),
        _row(lower_teeth, treated, selected, on_select, False),
        rx.text("ขากรรไกรล่าง", size="1", weight="bold", color="var(--slate-10)", align="center", width="100%"),
        width="100%",
        spacing="2",
    )


def legend() -> rx.Component:
    def item(color: str, border: str, text: str):
        return rx.hstack(rx.box(width="14px", height="14px", border_radius="4px", background_color=color, border=border),
                         rx.text(text, size="1", color="var(--slate-10)"), align="center", spacing="1")

    return rx.hstack(
        item("#ffffff", "1.5px solid var(--slate-6)", "ปกติ / ยังไม่มีประวัติ"),
        item("var(--orange-3)", "2px solid var(--orange-8)", "มีประวัติการรักษา"),
        item("var(--purple-9)", "2px solid var(--purple-10)", "ซี่ที่เลือก"),
        spacing="4",
        wrap="wrap",
    )


def dental_chart(treated, selected, on_select) -> rx.Component:
    """treated: Var list[str]; selected: Var str; on_select: handler that takes the tooth number."""
    return rx.vstack(
        rx.box(
            rx.box(
                _arch(PERMANENT_UPPER, PERMANENT_LOWER, treated, selected, on_select),
                # keep teeth tappable on phones: the chart scrolls sideways instead of shrinking
                min_width=["500px", "500px", "0"],
            ),
            width="100%",
            overflow_x="auto",
            padding=["10px", "16px"],
            border_radius="16px",
            background="linear-gradient(180deg, #FDF2F4 0%, #FFFFFF 50%, #FDF2F4 100%)",
            border="1px solid var(--pink-4)",
        ),
        rx.text("← เลื่อนซ้าย-ขวาเพื่อดูฟันทั้งปาก →", size="1", color="var(--slate-9)", display=["block", "block", "none"]),
        legend(),
        rx.text("เลขซี่ฟันเรียงจากซ้ายไปขวา: ฟันบน 1 → 16 และฟันล่าง 17 → 32",
                size="1", color="var(--slate-10)"),
        width="100%",
        spacing="3",
    )
