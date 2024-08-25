import asyncio
from collections.abc import AsyncGenerator
import json
import os
import traceback
# Google auth
from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests as gauth_requests
from requests_oauthlib import OAuth2Session

from sqlmodel import select
import reflex as rx

from .auth_state import AuthState, LOGIN_ROUTE, REGISTER_ROUTE
from .user import User

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]

class LoginRegState(AuthState):
    # State handler for registration and login pages.

    reg_success: bool = False
    error_message: str = ""

    # Handle email registration form submission and redirect to login page after registration.
    async def handle_registration(
        self, form_data
    ) -> AsyncGenerator[rx.event.EventSpec | list[rx.event.EventSpec] | None, None]:
        """Handle registration form on_submit.

        Set error_message appropriately based on validation results.

        Args:
            form_data: A dict of form fields and values.
        """
        with rx.session() as session:
            username = form_data["username"]
            email = form_data["email"]
            if not username:
                self.error_message = "Username cannot be empty"
                yield rx.set_focus("username")
                return
            existing_user = session.exec(
                select(User).where(User.email == email)
            ).one_or_none()
            if existing_user is not None:
                self.error_message = (
                    f"Email {email} is already registered. Try a different name"
                )
                yield [rx.set_value("email", ""), rx.set_focus("email")]
                return
            password = form_data["password"]
            if not password:
                self.error_message = "Password cannot be empty"
                yield rx.set_focus("password")
                return
            if password != form_data["confirm_password"]:
                self.error_message = "Passwords do not match"
                yield [
                    rx.set_value("confirm_password", ""),
                    rx.set_focus("confirm_password"),
                ]
                return
            # Create the new user and add it to the database.
            new_user = User()  # type: ignore
            new_user.username = username
            new_user.email = email
            new_user.password_hash = User.hash_password(password)
            new_user.enabled = True
            session.add(new_user)
            session.commit()
        # Set success and redirect to login page after a brief delay.
        self.error_message = ""
        self.reg_success = True
        yield
        await asyncio.sleep(0.5)
        yield [rx.redirect(LOGIN_ROUTE), LoginRegState.set_reg_success(False)]

    # Success callback after a Google login. Exchanges code for Oauth tokens and fetches user info.
    def on_google_auth(self, code: dict):
        try:
            google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=self.router.page.host)
            tokens = google.fetch_token(
                code=code['code'], 
                token_url="https://www.googleapis.com/oauth2/v4/token", 
                client_secret=GOOGLE_CLIENT_SECRET,
            )
            # Need to save tokens in the User record
            # Now get the user info
            google_user_info = verify_oauth2_token(
                tokens['id_token'],
                gauth_requests.Request(),
                GOOGLE_CLIENT_ID,
            )
            # Link to account with existing email, or create a new User
            with rx.session() as session:
                user = session.exec(select(User).where(User.google_sub == google_user_info["sub"])).first()
                if user is None:
                    # No existing Google user, look for email match
                    user = session.exec(select(User).where(User.email == google_user_info["email"])).first()
                    if user:
                        user.google_token = json.dumps(google_user_info)
                        user.google_sub = google_user_info["sub"]
                        session.add(user)
                        session.commit()
                        session.refresh(user)
                if user is None:
                    # No existing user, create a new one
                    user = User(
                        username=google_user_info["name"],
                        email=google_user_info["email"],
                        google_sub=google_user_info["sub"],
                        google_token=json.dumps(google_user_info),
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                if user and user.id:
                    self._login(user.id, user.username)
                self.error_message = ""
                return LoginRegState.redir()       # type: ignore             
        except:
            traceback.print_exc()
            self.error_message = "There was a problem logging in, please try again."

    def on_submit_email_login(self, form_data) -> rx.event.EventSpec:
        """Handle login form on_submit.

        Args:
            form_data: A dict of form fields and values.
        """
        self.error_message = ""
        email = form_data["email"]
        password = form_data["password"]
        with rx.session() as session:
            user = session.exec(
                select(User).where(User.email == email)
            ).one_or_none()
        if user is not None and not user.enabled:
            self.error_message = "This account is disabled."
            return rx.set_value("password", "")
        if user is None or not user.verify(password):
            self.error_message = "There was a problem logging in, please try again."
            return rx.set_value("password", "")
        if (
            user is not None
            and user.id is not None
            and user.enabled
            and user.verify(password)
        ):
            # mark the user as logged in
            self._login(user.id, user.username)
        self.error_message = ""
        return LoginRegState.redir()  # type: ignore

