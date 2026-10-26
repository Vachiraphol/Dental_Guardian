"""Every page registers itself with @rx.page; importing its module here adds it to the app."""

from . import (
    change_password,
    forgot_password,
    home,
    login,
    privacy,
    profile,
    profile_edit,
    register,
)
