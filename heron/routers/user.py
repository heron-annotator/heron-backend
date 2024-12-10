from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from heron.config import settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()
_hasher = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserRegister(UserBase):
    password: str

    model_config = {"extra": "forbid"}


class UserDB(UserBase):
    id: str
    password_hash: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Temp stuff to simulate a DB
_last_id: int = 0
_users: dict[str, UserDB] = {}


@router.post("/register")
def register(user: UserRegister):
    global _last_id
    global _users
    hash = _hasher.hash(user.password)
    id = str(_last_id)
    # NOTE: We're not checking for username clashes, but whatever for now
    _users[id] = UserDB(
        id=id,
        username=user.username,
        email=user.email,
        password_hash=hash,
    )
    _last_id += 1


def create_token(*, data: dict, expires_delta: timedelta) -> Token:
    """
    Create a new token ready to be returned.

    :param data: Extra data to encode in the JWT token
    :param expires_delta: Timedelta that specifies duration of the created token

    :return: Returns new Token instance
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    access_token = jwt.encode(to_encode, settings().secret_key, algorithm=JWT_ALGORITHM)
    return Token(access_token=access_token, token_type="bearer")


def authenticate_user(username: str, password: str) -> UserDB | None:
    """
    Authenticates user given username and password.

    If username and password match with existing user return that user.
    In all other cases returns None.

    :param username: User's username
    :param password: User's non hashed password

    :return: Return UserDB instance if username and password match, else None.
    """
    for user in _users.values():
        if user.username != username:
            continue
        if _hasher.verify(user.password_hash, password):
            return user
    return None


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDB:
    """
    Get the current user from the token.

    :param token: Token to get user from
    :return: Returns UserDB instance if token is valid, else None.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings().secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = _users.get(user_id)
    if user is None:
        raise credentials_exception

    return user


@router.get("/user/me", response_model=UserBase)
def get_user(current_user: UserDB = Depends(get_current_user)):
    return current_user


@router.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expiration_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_token(data={"sub": user.id}, expires_delta=expiration_delta)
    return token
