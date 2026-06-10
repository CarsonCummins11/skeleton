import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from lib import db
from models.users import (
    ClientUser,
    Token,
    User,
    get_current_user,
    login_user,
    search_users,
)

router = APIRouter()


@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    logging.info(f"Logging in user: {form_data.username}")
    async with await db.open_db_connection() as connection:
        return await login_user(connection, form_data.username, form_data.password)


@router.get("/me")
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ClientUser:
    return current_user.to_client_user()


@router.get("/info/{username}")
async def user_info(username: str) -> ClientUser:
    async with await db.open_db_connection() as connection:
        usr = await User.load_from_username(connection, username)
        if not usr:
            raise HTTPException(status_code=404, detail="User not found")
        return usr.to_client_user()


@router.get("/search/{query}")
async def user_search(
    query: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[ClientUser]:
    async with await db.open_db_connection() as connection:
        users = await search_users(connection, query)
        return [u.to_client_user() for u in users]
