import secrets
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.app_models import User
from app.config import get_settings

SESSION_COOKIE = "session"

settings = get_settings()

# The cookie carries a signed username, not a session id: nothing to look up, and
# nothing to store. Swap this for a session table when you need server-side logout.
serializer = URLSafeTimedSerializer(settings.session_secret, salt=SESSION_COOKIE)


def authenticate(username: str, password: str) -> User | None:
    """Stands in for a users table. compare_digest, so the check is constant-time."""
    ok_user = secrets.compare_digest(username, settings.auth_username)
    ok_password = secrets.compare_digest(password, settings.auth_password)
    return User(username=username) if ok_user and ok_password else None


def start_session(response: Response, user: User) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        serializer.dumps(user.username),
        max_age=settings.session_max_age_s,
        httponly=True,  # JavaScript cannot read it, so XSS cannot steal it
        secure=settings.cookie_secure,  # https only
        samesite="lax",  # not sent on cross-site POSTs, which blunts CSRF
        path="/",
    )


def end_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def get_current_user(
    session: Annotated[
        str | None,
        Cookie(alias=SESSION_COOKIE, description="Signed session cookie."),
    ] = None,
) -> User:
    """Turns a cookie into 'this is user Alice', or refuses the request."""
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        username = serializer.loads(session, max_age=settings.session_max_age_s)
    except SignatureExpired as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired") from exc
    except BadSignature as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session") from exc
    return User(username=username)


CurrentUser = Annotated[User, Depends(get_current_user)]
