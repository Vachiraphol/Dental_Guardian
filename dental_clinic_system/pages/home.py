import reflex as rx
from dental_clinic_system.state import AuthState

def home() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Test Backend ระบบบัญชี", size="5"),
            
            rx.input(placeholder="Email", on_change=AuthState.set_email, value=AuthState.email),
            rx.input(placeholder="Password", type="password", on_change=AuthState.set_password, value=AuthState.password),
            rx.select(["patient", "dentist", "nurse"], on_change=AuthState.set_role, value=AuthState.role),
            
            rx.hstack(
                rx.button("Register", on_click=AuthState.register, color_scheme="blue"),
                rx.button("Login", on_click=AuthState.login, color_scheme="green"),
            ),
            
            rx.text(f"User ID: {AuthState.current_user_id} | Role: {AuthState.current_role}"),
        ),
        padding="2em"
    )