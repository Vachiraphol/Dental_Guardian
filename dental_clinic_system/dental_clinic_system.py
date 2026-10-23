import reflex as rx
from dental_clinic_system.pages.home import home

app = rx.App()
app.add_page(home, route="/")