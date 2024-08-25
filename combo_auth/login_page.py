"""Login page and authentication logic."""
import reflex as rx

from .auth_state import AuthState
from .login_state import LoginRegState, LOGIN_ROUTE, REGISTER_ROUTE, GOOGLE_CLIENT_ID
from .google_login import get_google_login_button


def home_login_page() -> rx.Component:
    return rx.fragment(
        rx.chakra.vstack(
            rx.chakra.heading("Example Home/Login", font_size="2em"),
            rx.cond(
                AuthState.is_authenticated,
                rx.chakra.button(
                    "Go to Dashboard", 
                    on_click=rx.redirect("/home"),
                    margin_bottom="2em !important",
                ),
            ),
            spacing="1.5em",
            padding_top="10%",
        ),
        rx.chakra.form(
            rx.chakra.input(placeholder="email", id="email"),
            rx.chakra.password(placeholder="password", id="password"),
            rx.chakra.button("Login", type_="submit"),
            width="80vw",
            on_submit=LoginRegState.on_submit_email_login,
        ),
        get_google_login_button(
            client_id=GOOGLE_CLIENT_ID, 
            on_success=LoginRegState.on_google_auth,
        ),
    )


@rx.page(route=LOGIN_ROUTE)
def login_page() -> rx.Component:
    """Render the login page.

    Returns:
        A reflex component.
    """

    return rx.fragment(
        rx.chakra.vstack(
            rx.cond(  # conditionally show error messages
                LoginRegState.error_message != "",
                rx.chakra.text(LoginRegState.error_message),
            ),
            home_login_page(),
            rx.chakra.link("Create new account", href=REGISTER_ROUTE),
            padding_top="10vh",
        ),
    )


