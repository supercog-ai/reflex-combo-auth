"""New user registration form and validation logic."""
from __future__ import annotations

import reflex as rx
from sqlmodel import select

from .login_page import LoginRegState, REGISTER_ROUTE


@rx.page(route=REGISTER_ROUTE)
def registration_page() -> rx.Component:
    """Render the registration page.

    Returns:
        A reflex component.
    """
    register_form = rx.chakra.form(
        rx.chakra.input(placeholder="username", id="username"),
        rx.chakra.input(placeholder="email", id="email"),
        rx.chakra.password(placeholder="password", id="password"),
        rx.chakra.password(placeholder="confirm", id="confirm_password"),
        rx.chakra.button("Register", type_="submit"),
        width="80vw",
        on_submit=LoginRegState.handle_registration,
    )
    return rx.fragment(
        rx.cond(
            LoginRegState.reg_success,
            rx.chakra.vstack(
                rx.chakra.text("Registration successful!"),
                rx.chakra.spinner(),
            ),
            rx.chakra.vstack(
                rx.cond(  # conditionally show error messages
                    LoginRegState.error_message != "",
                    rx.chakra.text(LoginRegState.error_message),
                ),
                register_form,
                padding_top="10vh",
            ),
        )
    )
