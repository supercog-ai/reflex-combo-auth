"""
Top-level State for the App.

Authentication data is stored in the base State class so that all substates can
access it for verifying access to event handlers and computed vars.
"""
import datetime

from sqlmodel import select, Session
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token

import reflex as rx

from .auth_session import AuthSession
from .user import User, ANON_SENITINEL

LOGIN_ROUTE = "/"
REGISTER_ROUTE = "/register"

AUTH_TOKEN_LOCAL_STORAGE_KEY = "_auth_token"
DEFAULT_AUTH_SESSION_EXPIRATION_DELTA = datetime.timedelta(days=7)


class AuthState(rx.State):
    # The auth_token is stored in local storage to persist across tab and browser sessions.
    auth_token: str = rx.SessionStorage(name=AUTH_TOKEN_LOCAL_STORAGE_KEY)
    user: User = User(username=ANON_SENITINEL) 
    redirect_to: str = ""

    @rx.var(cache=True)
    def authenticated_user(self) -> User:
        """The currently authenticated user, or a dummy user if not authenticated.

        Returns:
            A User instance with id=-1 if not authenticated, or the User instance
            corresponding to the currently authenticated user.
        """
        with rx.session() as session:
            result = session.exec(
                select(User, AuthSession).where(
                    AuthSession.session_id == self.auth_token,
                    AuthSession.expiration
                    >= datetime.datetime.now(datetime.timezone.utc),
                    User.id == AuthSession.user_id,
                ),
            ).first()
            if result:
                user, auth_session = result
                self.user = user
                return user
        return User(username=ANON_SENITINEL)

    @rx.var(cache=True)
    def is_authenticated(self) -> bool:
        """Whether the current user is authenticated.

        Returns:
            True if the authenticated user has a positive user ID, False otherwise.
        """
        return not self.authenticated_user.is_anonymous()

    def do_logout(self) -> None:
        """Destroy AuthSessions associated with the auth_token."""
        with rx.session() as session:
            for auth_session in session.exec(
                select(AuthSession).where(AuthSession.session_id == self.auth_token)
            ).all():
                session.delete(auth_session)
            session.commit()
        self.auth_token = self.auth_token

    def scavange_auth_session(self, session: Session, session_id: str):
        statement = select(AuthSession).where(AuthSession.session_id == session_id)
        result = session.exec(statement).first()       
        if result:
            # Delete the record if found
            session.delete(result)
            session.commit()

    def redir(self) -> rx.event.EventSpec | None:
        """Redirect to the redirect_to route if logged in, or to the login page if not."""
        if not self.is_hydrated:
            # wait until after hydration to ensure auth_token is known
            return AuthState.redir()  # type: ignore
        print("Got in AuthState redir")
        page = self.router.page.path
        if not self.is_authenticated and page != LOGIN_ROUTE:
            self.redirect_to = page
            return rx.redirect(LOGIN_ROUTE)
        elif page == LOGIN_ROUTE:
            return rx.redirect(self.redirect_to or "/home")

    def _login(
        self,
        user_id: str,
        username: str,
        expiration_delta: datetime.timedelta = DEFAULT_AUTH_SESSION_EXPIRATION_DELTA,
    ) -> None:
        """Create an AuthSession for the given user_id.

        If the auth_token is already associated with an AuthSession, it will be
        logged out first.

        Args:
            user_id: The user ID to associate with the AuthSession.
            expiration_delta: The amount of time before the AuthSession expires.
        """
        if self.is_authenticated:
            self.do_logout()
        if username == ANON_SENITINEL:
            return
        self.auth_token = self.auth_token or self.router.session.client_token
        with rx.session() as session:
            self.scavange_auth_session(session, self.auth_token)
            session.add(
                AuthSession(  # type: ignore
                    user_id=user_id,
                    session_id=self.auth_token,
                    expiration=datetime.datetime.now(datetime.timezone.utc)
                    + expiration_delta,
                )
            )
            session.commit()

    def home_page_load(self):
        if self.user.is_anonymous():
            return
        print("Home page load handler is running")

def require_login(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Decorator to require authentication before rendering a page. This
       decorator checks the "local user" authentication state - it says nothing
       about the Google auth or other browser state.

    Args:
        page: The page to wrap.

    Returns:
        The wrapped page component.
    """

    def protected_page():
        return rx.fragment(
            rx.cond(
                AuthState.is_hydrated & AuthState.is_authenticated,  # type: ignore
                page(),
                rx.chakra.center(
                    # When this spinner mounts, it will redirect to the login page
                    rx.chakra.spinner(on_mount=AuthState.redir),
                ),
            )
        )

    protected_page.__name__ = page.__name__
    return protected_page
