from passlib.context import CryptContext
from uuid import uuid4 as get_uuid4
import uuid
from sqlmodel import Field

import reflex as rx

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ANON_SENITINEL = "__anonymous__"

def uuidcol():
    return str(get_uuid4())

class User(
    rx.Model,
    table=True,  # type: ignore
):
    """A local User model with bcrypt password hashing."""
    id: str = Field(default_factory=uuidcol, primary_key=True)

    username: str = Field(nullable=False, index=True)
    email: str = Field(unique=True, nullable=False, index=True)
    password_hash: str = Field(nullable=True)
    enabled: bool = True
    google_token: str = Field(nullable=True)
    google_sub: str = Field(nullable=True)

    @staticmethod
    def hash_password(secret: str) -> str:
        """Hash the secret using bcrypt.

        Args:
            secret: The password to hash.

        Returns:
            The hashed password.
        """
        return pwd_context.hash(secret)

    def verify(self, secret: str) -> bool:
        """Validate the user's password.

        Args:
            secret: The password to check.

        Returns:
            True if the hashed secret matches this user's password_hash.
        """
        return pwd_context.verify(
            secret,
            self.password_hash,
        )

    def is_anonymous(self) -> bool:
        """Whether this user is an anonymous user."""
        return self.username == ANON_SENITINEL
