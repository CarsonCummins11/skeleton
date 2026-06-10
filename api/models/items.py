from typing import Optional

import asyncpg
from pydantic import BaseModel

import lib.time
from lib import db
from lib.ids import IdType, generate_id


class Item(BaseModel):
    id: str
    owner_username: str
    title: str
    description: Optional[str]
    created_at: int

    @classmethod
    async def create(
        cls,
        connection: asyncpg.Connection,
        owner_username: str,
        title: str,
        description: Optional[str] = None,
    ) -> "Item":
        item_id = generate_id(IdType.ITEM)
        now = lib.time.usec_timestamp()
        await db.execute_query(
            connection,
            "INSERT INTO items (id, owner_username, title, description, created_at) VALUES ($1, $2, $3, $4, $5)",
            item_id,
            owner_username,
            title,
            description,
            now,
        )
        return cls(
            id=item_id,
            owner_username=owner_username,
            title=title,
            description=description,
            created_at=now,
        )

    @classmethod
    async def get(cls, connection: asyncpg.Connection, item_id: str) -> Optional["Item"]:
        row = await db.query_for_one(
            connection, "SELECT * FROM items WHERE id = $1", item_id
        )
        return cls(**row) if row else None

    @classmethod
    async def list_for_user(
        cls, connection: asyncpg.Connection, username: str
    ) -> list["Item"]:
        rows = await db.query_for_all(
            connection,
            "SELECT * FROM items WHERE owner_username = $1 ORDER BY created_at DESC",
            username,
        )
        return [cls(**row) for row in rows]

    async def delete(self, connection: asyncpg.Connection):
        await db.execute_query(connection, "DELETE FROM items WHERE id = $1", self.id)
