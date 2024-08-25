import reflex as rx

from .auth_state import AuthState, require_login

@rx.page(route="/home", on_load=AuthState.home_page_load)
@require_login
def protected_homepage() -> rx.Component:
    """Render a protected page.

    The `require_login` decorator will redirect to the login page if the user is
    not authenticated.

    Returns:
        A reflex component.
    """
    return rx.chakra.vstack(
        rx.chakra.heading(
            "Logged in Page for ", AuthState.authenticated_user.username, font_size="2em"
        ),
        rx.chakra.text("Email: " +AuthState.authenticated_user.email),
        rx.chakra.link("Settings", href="/settings"),
        rx.chakra.link("Logout", href="/", on_click=AuthState.do_logout),
        rx.chakra.link("Back to slash", href="/"),
    )

