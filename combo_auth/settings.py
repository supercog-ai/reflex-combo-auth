import reflex as rx

from .auth_state import AuthState, require_login

@rx.page(route="/settings")
@require_login
def settings_page() -> rx.Component:
    """Render a protected page.

    The `require_login` decorator will redirect to the login page if the user is
    not authenticated.

    Returns:
        A reflex component.
    """
    return rx.chakra.vstack(
        rx.chakra.heading(
            "Settings Page for ", AuthState.authenticated_user.username, font_size="2em"
        ),
        rx.chakra.link("Home", href="/home"),
        rx.chakra.text("Email: " +AuthState.authenticated_user.email),
        rx.chakra.link("Logout", href="/", on_click=AuthState.do_logout),
        bg="lightblue",
    )

