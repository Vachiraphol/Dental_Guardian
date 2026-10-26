"""Every page registers itself with @rx.page; importing its module here adds it to the app."""

from . import (
    forgot_password,
    home,
    login,
    profile,
    profile_edit,
    register,
)
