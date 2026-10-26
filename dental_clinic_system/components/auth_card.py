"""Card used by the login, register and forgot-password pages."""

import reflex as rx

from dental_clinic_system.components.brand import logo


def auth_card(icon: str, title: str, subtitle: str, *children: rx.Component, max_width: str = "460px") -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                logo("72px"),
                rx.heading(title, size="6", align="center"),
                rx.text(subtitle, size="2", color="var(--slate-10)", align="center"),
                *children,
                width="100%",
                align="center",
                spacing="3",
            ),
            width="100%",
            max_width=max_width,
            padding=["24px", "32px"],
            box_shadow="0 10px 40px -10px rgba(0,0,0,0.12)",
        ),
        width="100%",
    )


def password_input(name: str, placeholder: str = "••••••••", **props) -> rx.Component:
    return rx.input(name=name, type="password", placeholder=placeholder, size="3", width="100%", required=True, **props)
