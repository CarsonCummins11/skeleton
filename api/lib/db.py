import os
from typing import Any, Dict, List, Optional

import asyncpg

_db_connection_pool: Optional[asyncpg.Pool] = None


async def open_db_connection_pool():
    global _db_connection_pool
    _db_connection_pool = await asyncpg.create_pool(os.environ.get("DATABASE_URL"))


async def close_db_connection_pool():
    assert _db_connection_pool is not None
    await _db_connection_pool.close()


async def open_db_connection():
    assert _db_connection_pool is not None
    return _db_connection_pool.acquire()


async def query_for_all(
    connection: asyncpg.Connection, query: str, *args
) -> List[Dict[str, Any]]:
    rows = await connection.fetch(query, *args)
    return [dict(row) for row in rows]


async def query_for_one(connection: asyncpg.Connection, query: str, *args):
    row = await connection.fetchrow(query, *args)
    return dict(row) if row else None


async def execute_query(connection: asyncpg.Connection, query: str, *args):
    await connection.execute(query, *args)
