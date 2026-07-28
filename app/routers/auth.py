from fastapi import APIRouter, HTTPException, Response, status

from app.app_models import LoginRequest, User
from app.security import CurrentUser, authenticate, end_session, start_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", summary="Start a session")
def login(body: LoginRequest, response: Response) -> User:
    user = authenticate(body.username, body.password)
    if user is None:
        # Same message for both failures: never reveal which half was wrong.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    start_session(response, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="End the session")
def logout(response: Response) -> None:
    end_session(response)


@router.get("/me", summary="Who the cookie says you are")
def me(user: CurrentUser) -> User:
    return user
