import uuid
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Annotated

import asyncpg
import jwt
from argon2 import PasswordHasher
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from heron.config import settings
from heron.db import get_connection
from heron.db import user as db_user

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = getLogger(__name__)

router = APIRouter()
_hasher = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserRegister(UserBase):
    password: str

    model_config = {"extra": "forbid"}


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register")
async def register(
    user: UserRegister, conn: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    # Not the best way to handle email and username uniqueness, it does the job
    # for now.
    # I'll find a more elegant way later on.
    if await db_user.email_exists(conn, user.email):
        logger.info(f"Email {user.email} already exists")
        raise HTTPException(status_code=400, detail="Email already in use")

    if await db_user.username_exists(conn, user.username):
        logger.info(f"Username {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already in use")

    id = uuid.uuid4()
    try:
        await db_user.create(
            conn,
            db_user.User(
                id=id,
                username=user.username,
                email=user.email,
                password_hash=_hasher.hash(user.password),
            ),
        )
    except Exception as exc:
        logger.exception(exc)
        raise HTTPException(status_code=500, detail="Failed to register user")

    return {"user_id": id}


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


async def authenticate_user(
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    username: str,
    password: str,
) -> db_user.User | None:
    """
    Authenticates user given username and password.

    If username and password match with existing user return that user.
    In all other cases returns None.

    :param username: User's username
    :param password: User's non hashed password

    :return: Return User instance if username and password match, else None.
    """
    user = await db_user.get_by_username(conn, username)
    if user and _hasher.verify(user.password_hash, password):
        return user
    return None


async def get_current_user(
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    token: str = Depends(oauth2_scheme),
) -> db_user.User:
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

    user = await db_user.get_by_id(conn, uuid.UUID(user_id))
    if user is None:
        raise credentials_exception

    return user


@router.get("/user/me")
def get_user(current_user: db_user.User = Depends(get_current_user)):
    return UserBase(username=current_user.username, email=current_user.email)


@router.post("/token")
async def login(
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = await authenticate_user(conn, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expiration_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_token(data={"sub": str(user.id)}, expires_delta=expiration_delta)
    return token
