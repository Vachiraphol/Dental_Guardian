import reflex as rx
from . import pages  # noqa: F401  (registers every @rx.page)

class State(rx.State):
    """The app state."""
    pass

app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="large",
        accent_color="purple",
        font_family="Kanit",
    ),
    stylesheets=["/styles.css"],
    head_components=[
        rx.el.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
        rx.el.link(rel="icon", type="image/png", href="/favicon.png"),
    ]
)
