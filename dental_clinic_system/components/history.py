"""Pieces shared by the treatment-history pages (SRS 5.4)."""

import reflex as rx

from dental_clinic_system.components.ui import card, medical_flags
from dental_clinic_system.state import AppState


def chart_badge() -> rx.Component:
    """Dropdown สลับโหมดผังฟันระหว่างฟันแท้ (ผู้ใหญ่) และฟันน้ำนม (เด็ก)"""
    return rx.select.root(
        rx.select.trigger(
            color_scheme=rx.cond(AppState.chart_mode == "child", "pink", "purple"),
            variant="soft",
            size="1",
            cursor="pointer",
        ),
        rx.select.content(
            rx.select.item("ผังฟันแท้ (32 ซี่)", value="adult"),
            rx.select.item("ผังฟันน้ำนม (20 ซี่)", value="child"),
        ),
        value=AppState.chart_mode,
        on_change=AppState.set_chart_mode,
    )


def entry_item(e, show_tooth: bool = True) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(e["ts_th"], weight="bold", size="2"),
            *([rx.badge(e["tooth_label"], color_scheme="purple", variant="soft")] if show_tooth else []),
            rx.spacer(),
            rx.badge(e["procedure"], color_scheme="blue"),
            width="100%",
            align="center",
            wrap="wrap",
        ),
        rx.text(e["icd_th"], rx.text.span(" (" + e["icd"] + ")", color="var(--slate-9)"), size="2", weight="medium", margin_top="6px"),
        rx.cond(e["note"] != "", rx.text(e["note"], size="2", color="var(--slate-11)")),
        rx.text(e["dentist"], size="1", color="var(--slate-10)", margin_top="4px"),
        padding="12px",
        background_color="var(--slate-2)",
        border_left="3px solid var(--primary-color)",
        border_radius="8px",
        width="100%",
    )


def patient_picker() -> rx.Component:
    p = AppState.selected_patient
    return card(
        rx.flex(
            rx.vstack(
                rx.text("ผู้ป่วย", size="1", color="var(--slate-10)"),
                rx.select(AppState.patient_options, value=AppState.selected_patient_option, on_change=AppState.select_patient,
                          placeholder="ยังไม่มีผู้ป่วย", size="3"),
                spacing="1",
                width=["100%", "100%", "320px"],
                class_name="dg-field",
            ),
            rx.cond(
                AppState.has_patients,
                rx.vstack(
                    rx.hstack(rx.text(p["full_name"], weight="bold", size="4"), rx.badge(p["id"], color_scheme="gray"), align="center"),
                    rx.text(p["gender"] + " · อายุ " + p["age"] + " ปี · โทร " + p["phone"], size="2", color="var(--slate-10)"),
                    medical_flags(p["disease"], p["allergy"]),
                    spacing="1",
                    flex="1",
                ),
            ),
            gap="20px",
            align="center",
            wrap="wrap",
            width="100%",
        ),
        padding="18px",
    )
