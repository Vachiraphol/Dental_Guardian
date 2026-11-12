import reflex as rx

from dental_clinic_system.state import (
    AppState,
    MOLARS,
    PERMANENT_LOWER,
    PERMANENT_UPPER,
    PRIMARY_TEETH_LOWER,
    PRIMARY_TEETH_UPPER,
    tooth_label,
)


def _tooth(t: str, treated, selected, on_select, upper: bool) -> rx.Component:
    molar = t in MOLARS
    is_selected = selected == t
    is_treated = treated.contains(t)
    is_child = AppState.chart_mode == "child"

    normal_bg = rx.cond(is_child, "var(--pink-2)", "#ffffff")
    normal_border = rx.cond(is_child, "1.5px solid var(--pink-7)", "1.5px solid var(--slate-6)")

    selected_bg = rx.cond(is_child, "var(--pink-9)", "var(--purple-9)")
    selected_border = rx.cond(is_child, "2px solid var(--pink-10)", "2px solid var(--purple-10)")
    hover_border = rx.cond(is_child, "var(--pink-8)", "var(--purple-8)")

    return rx.tooltip(
        rx.vstack(
            *([rx.text(t, size="1", color="var(--slate-10)")] if not upper else []),
            rx.box(
                rx.cond(
                    is_treated,
                    rx.box(
                        width="6px",
                        height="6px",
                        border_radius="50%",
                        background_color=rx.cond(is_selected, "white", "var(--orange-9)"),
                    ),
                ),
                width="100%",
                height="34px" if molar else "28px",
                display="flex",
                align_items="center",
                justify_content="center",
                border_radius="8px 8px 14px 14px" if upper else "14px 14px 8px 8px",
                border=rx.cond(
                    is_selected,
                    selected_border,
                    rx.cond(is_treated, "2px solid var(--orange-8)", normal_border),
                ),
                background_color=rx.cond(
                    is_selected,
                    selected_bg,
                    rx.cond(is_treated, "var(--orange-3)", normal_bg),
                ),
                transition="all 0.15s ease",
                _hover={"transform": "scale(1.08)", "border_color": hover_border},
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
    is_child = AppState.chart_mode == "child"
    return rx.vstack(
        rx.hstack(
            rx.text("ขวาของผู้ป่วย", size="1", color="var(--slate-9)"),
            rx.spacer(),
            rx.text(
                rx.cond(is_child, "ขากรรไกรบน (ฟันน้ำนม)", "ขากรรไกรบน"),
                size="1",
                weight="bold",
                color=rx.cond(is_child, "var(--pink-11)", "var(--slate-10)"),
            ),
            rx.spacer(),
            rx.text("ซ้ายของผู้ป่วย", size="1", color="var(--slate-9)"),
            width="100%",
        ),
        _row(upper_teeth, treated, selected, on_select, True),
        rx.divider(),
        _row(lower_teeth, treated, selected, on_select, False),
        rx.text(
            rx.cond(is_child, "ขากรรไกรล่าง (ฟันน้ำนม)", "ขากรรไกรล่าง"),
            size="1",
            weight="bold",
            color=rx.cond(is_child, "var(--pink-11)", "var(--slate-10)"),
            align="center",
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def legend() -> rx.Component:
    is_child = AppState.chart_mode == "child"

    def item(color: str, border: str, text: str):
        return rx.hstack(
            rx.box(width="14px", height="14px", border_radius="4px", background_color=color, border=border),
            rx.text(text, size="1", color="var(--slate-10)"),
            align="center",
            spacing="1",
        )

    return rx.hstack(
        item("#ffffff", "1.5px solid var(--slate-6)", "ปกติ / ยังไม่มีประวัติ"),
        item("var(--orange-3)", "2px solid var(--orange-8)", "มีประวัติการรักษา"),
        rx.hstack(
            rx.box(
                width="14px",
                height="14px",
                border_radius="4px",
                background_color=rx.cond(is_child, "var(--pink-9)", "var(--purple-9)"),
                border=rx.cond(is_child, "2px solid var(--pink-10)", "2px solid var(--purple-10)"),
            ),
            rx.text("ซี่ที่เลือก", size="1", color="var(--slate-10)"),
            align="center",
            spacing="1",
        ),
        # แสดงกล่องสีชมพูใน Legend ระบุฟันน้ำนม
        rx.cond(
            is_child,
            rx.hstack(
                rx.box(
                    width="14px",
                    height="14px",
                    border_radius="4px",
                    background_color="var(--pink-2)",
                    border="1.5px solid var(--pink-7)",
                ),
                rx.text("ฟันน้ำนม", size="1", color="var(--pink-11)", weight="medium"),
                align="center",
                spacing="1",
            ),
        ),
        spacing="4",
        wrap="wrap",
    )


def dental_chart(treated, selected, on_select) -> rx.Component:
    """treated: Var list[str]; selected: Var str; on_select: handler that takes the tooth number."""
    is_child = AppState.chart_mode == "child"

    arch_permanent = _arch(PERMANENT_UPPER, PERMANENT_LOWER, treated, selected, on_select)
    arch_primary = _arch(PRIMARY_TEETH_UPPER, PRIMARY_TEETH_LOWER, treated, selected, on_select)

    return rx.vstack(
        rx.box(
            rx.box(
                rx.cond(is_child, arch_primary, arch_permanent),
                min_width=["500px", "500px", "0"],
            ),
            width="100%",
            overflow_x="auto",
            padding=["10px", "16px"],
            border_radius="16px",
            background=rx.cond(
                is_child,
                "linear-gradient(180deg, #FFF1F2 0%, #FFFFFF 50%, #FFF1F2 100%)",
                "linear-gradient(180deg, #FDF2F4 0%, #FFFFFF 50%, #FDF2F4 100%)",
            ),
            border=rx.cond(is_child, "1.5px solid var(--pink-6)", "1px solid var(--pink-4)"),
        ),
        rx.text("← เลื่อนซ้าย-ขวาเพื่อดูฟันทั้งปาก →", size="1", color="var(--slate-9)", display=["block", "block", "none"]),
        legend(),
        rx.text(
            rx.cond(
                is_child,
                "เลขซี่ฟันเรียงจากซ้ายไปขวา (ฟันน้ำนม): ฟันบน 55 → 65 และฟันล่าง 85 → 75",
                "เลขซี่ฟันเรียงจากซ้ายไปขวา: ฟันบน 18 → 28 และฟันล่าง 48 → 38",
            ),
            size="1",
            color="var(--slate-10)",
        ),
        width="100%",
        spacing="3",
    )