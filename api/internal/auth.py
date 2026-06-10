from typing import Optional
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi import Request, Response
from models.users import User, get_password_hash
from lib import db

# Hardcoded intranet users with plain text passwords
INTRANET_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "full_name": "System Administrator",
        "profile_image_url": "https://carsoncummins.com/ico.png",
    },
    "carson": {
        "username": "carson",
        "password": "password",
        "full_name": "Carson Cummins",
        "profile_image_url": "https://carsoncummins.com/ico.png",
    },
    "dev": {
        "username": "dev",
        "password": "password",
        "full_name": "Developer",
        "profile_image_url": "https://carsoncummins.com/ico.png",
    },
}


def verify_intranet_user(username: str, password: str) -> Optional[dict]:
    """Verify intranet user credentials against hardcoded users"""
    if username not in INTRANET_USERS:
        return None

    user_data = INTRANET_USERS[username]
    if password == user_data["password"]:
        return user_data

    return None


async def get_current_intranet_user(request: Request) -> Optional[dict]:
    """Get current intranet user from session"""
    session = request.session
    username = session.get("intranet_user")
    if username and username in INTRANET_USERS:
        return INTRANET_USERS[username]
    return None


async def require_intranet_auth(request: Request) -> dict:
    """Require intranet authentication, redirect to login if not authenticated"""
    user = await get_current_intranet_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"Location": "/internal/login"},
        )
    return user


def create_intranet_session(request: Request, username: str):
    """Create intranet session for authenticated user"""
    request.session["intranet_user"] = username


def clear_intranet_session(request: Request):
    """Clear intranet session"""
    request.session.clear()
