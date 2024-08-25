# Combined Email and Google Auth

This is a demo Reflex app that combines Google and Email auth. I wanted to do do auth
this way for my app (supercog.ai), but working out a way to combine the "local auth"
and "google auth" Reflex examples took a lot of fiddling.

This example also retrieves the Google refresh token as part of the Oauth flow, which
is not supported by the original example. This is required if you want sessions that
last longer than 1 hour (as I recall).

## Running

Copy `.env.exmaple` and put your client ID and secret in a `.env` file.

Then run with:

    dotenv run reflex run

## Pages

    / - non-authenticated   - "home Login page"

In `login_page.py`. Shows the login form, link to register, and shows a link to
go to protected routes if we find the user is already auth'd.

    /register               - register page
    /home                   - Logged in home page
    /settings               - Second logged in page

## Objects

**AuthState**

The top of the rx.State tree, this class keeps the user authentication state and
the current user. Any states used by logged in pages should inherit from this state.

**LoginRegState**

This state handles events specific to user registration and login, 
supporting both Email and Google Auth.

**User**

This is the standard User records. It records the email/password or the information
about the Google login.

**AuthSession**

An AuthSession binds the logged in User to the "browser session" so that the user
stays logged in. We create this upon user login, and then as long as the
user presents their "auth_token" from the browser then they will remain logged in.

The `authenticated_user` calcuated var looks up the User record from the
AuthSession based on the auth_token value.

**Browser storage**

SessionStorage.auth_token = the session id, saved inside AuthSession to link to User

