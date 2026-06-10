from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from lib import db
from models.items import Item
from models.users import User, get_current_user
from pydantic import BaseModel

router = APIRouter()


class CreateItemRequest(BaseModel):
    title: str
    description: Optional[str] = None


@router.post("/")
async def create_item(
    body: CreateItemRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Item:
    async with await db.open_db_connection() as connection:
        return await Item.create(connection, owner_username=current_user.username, title=body.title, description=body.description)


@router.get("/")
async def list_items(
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[Item]:
    async with await db.open_db_connection() as connection:
        return await Item.list_for_user(connection, current_user.username)


@router.get("/{item_id}")
async def get_item(
    item_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Item:
    async with await db.open_db_connection() as connection:
        item = await Item.get(connection, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.owner_username != current_user.username:
            raise HTTPException(status_code=403, detail="Not authorized")
        return item


@router.delete("/{item_id}")
async def delete_item(
    item_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    async with await db.open_db_connection() as connection:
        item = await Item.get(connection, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.owner_username != current_user.username:
            raise HTTPException(status_code=403, detail="Not authorized")
        await item.delete(connection)
        return {"status": "deleted"}
