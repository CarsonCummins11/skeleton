import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Optional, cast

import asyncpg
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from lib import db
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # one week


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class ClientUser(BaseModel):
    username: str
    full_name: str
    profile_image_url: str


class User(BaseModel):
    username: str
    hashed_password: str
    full_name: str
    profile_image_url: str

    @classmethod
    async def load_from_username(cls, connection: asyncpg.Connection, username: str):
        user_row = await db.query_for_one(
            connection, "SELECT * FROM users WHERE username = $1", username
        )
        return cls(**user_row) if user_row else None

    @classmethod
    async def load_from_id(cls, connection: asyncpg.Connection, id: str):
        user_row = await db.query_for_one(
            connection, "SELECT * FROM users WHERE id = $1", id
        )
        return cls(**user_row) if user_row else None

    async def create(self, connection: asyncpg.Connection):
        await connection.execute(
            "INSERT INTO users (username, full_name, hashed_password, profile_image_url) VALUES ($1, $2, $3, $4)",
            self.username,
            self.full_name,
            self.hashed_password,
            self.profile_image_url,
        )

    def to_client_user(self) -> ClientUser:
        return ClientUser(
            username=self.username,
            full_name=self.full_name,
            profile_image_url=self.profile_image_url,
        )


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(
    db: asyncpg.Connection, username: str, password: str
) -> Optional[User]:
    user = await User.load_from_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: Dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = cast(str, payload.get("sub"))
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    if not token_data.username:
        raise credentials_exception
    async with await db.open_db_connection() as connection:
        user = await User.load_from_username(connection, token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def login_user(
    connection: asyncpg.Connection, username: str, password: str
) -> Token:
    user = await authenticate_user(connection, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logging.info(f"User {user.username} logged in successfully.")
    return Token(access_token=access_token, token_type="bearer")


async def search_users(connection: asyncpg.Connection, query: str) -> list[User]:
    query = f"%{query}%"
    users = await db.query_for_all(
        connection,
        "SELECT * FROM users WHERE username ILIKE $1",
        query,
    )
    return [User(**user) for user in users]
