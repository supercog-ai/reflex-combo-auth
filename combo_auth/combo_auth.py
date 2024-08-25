"""Main app module to demo local authentication."""
import reflex as rx

from .register_page import registration_page as registration_page
from .login_page import login_page
from .home_page import protected_homepage
from .settings import settings_page

from .user import User

app = rx.App()
