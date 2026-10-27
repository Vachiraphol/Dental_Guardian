"""Step indicator shared by the booking pages."""

import reflex as rx


def step_bar(current: int) -> rx.Component:
    def step(n: int, text: str):
        done = n <= current
        return rx.hstack(
            rx.center(rx.text(str(n), size="1", weight="bold", color="white" if done else "var(--slate-10)"),
                      width="26px", height="26px", border_radius="50%",
                      background_color="var(--primary-color)" if done else "var(--slate-4)"),
            rx.text(text, size="2", weight="bold" if n == current else "regular",
                    color="var(--slate-12)" if done else "var(--slate-10)"),
            align="center",
            spacing="2",
        )

    return rx.hstack(
        step(1, "เลือกวัน/เวลา"), rx.box(height="2px", width="32px", background_color="var(--slate-5)"),
        step(2, "สรุปและยืนยัน"), rx.box(height="2px", width="32px", background_color="var(--slate-5)"),
        step(3, "ใบจองคิว"),
        align="center",
        justify="center",
        wrap="wrap",
        width="100%",
        spacing="3",
    )
