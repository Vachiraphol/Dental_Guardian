"""Every page registers itself with @rx.page; importing its module here adds it to the app."""

from . import (
    booking,
    booking_summary,
    change_password,
    forgot_password,
    home,
    login,
    my_appointments,
    privacy,
    profile,
    profile_edit,
    register,
)
