import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Optional, cast

import redis.asyncio as redis

_cache_redis_connection_url = os.environ.get("CACHE_REDIS_URL")
_cache_redis_connection_pool = (
    redis.ConnectionPool().from_url(
        _cache_redis_connection_url,
    )
    if _cache_redis_connection_url
    else None
)


# context manager to get a redis connection
@asynccontextmanager
async def cache_redis_connection() -> AsyncGenerator[redis.Redis]:
    if _cache_redis_connection_pool is None:
        raise RuntimeError(
            "Cache Redis connection pool is not initialized. Please check your CACHE_REDIS_URL environment variable."
        )
    else:
        redis_connection = redis.Redis(
            decode_responses=True,
        ).from_pool(_cache_redis_connection_pool)
        try:
            yield redis_connection
        finally:
            await redis_connection.close()


_pubsub_redis_connection_url = os.environ.get("PUBSUB_REDIS_URL")
_pubsub_redis_connection_pool = (
    redis.ConnectionPool().from_url(
        _pubsub_redis_connection_url,
    )
    if _pubsub_redis_connection_url
    else None
)


@asynccontextmanager
async def pubsub_redis_connection() -> AsyncGenerator[redis.Redis]:
    if _pubsub_redis_connection_pool is None:
        raise RuntimeError(
            "Pubsub Redis connection pool is not initialized. Please check your PUBSUB_REDIS_URL environment variable."
        )
    else:
        redis_connection = redis.Redis(
            decode_responses=True,
        ).from_pool(_pubsub_redis_connection_pool)
        try:
            yield redis_connection
        finally:
            await redis_connection.close()


# Fucking redis returns union types for async stuff so we have to cast to make mypy happy
# which is so stupid, reimplementing here for Devxp reasons
# I also am adding optional redis_connection args and it will just grab it from the pool if not provided
# cuz redis doesn't care about conneciton locks so i care less about making devs reuse connections
# also I'm using diff redis clusters for cache and pubsub cuz those are different things so I want to have different configs / telemetry


async def hset(
    key: str, mapping: dict[str, Any], redis_connection: Optional[redis.Redis] = None
) -> None:
    if redis_connection is None:
        async with cache_redis_connection() as redis_conn:
            await cast(Awaitable[int], redis_conn.hset(key, mapping=mapping))
    else:
        await cast(Awaitable[int], redis_connection.hset(key, mapping=mapping))


async def rpush(
    key: str, value: Any, redis_connection: Optional[redis.Redis] = None
) -> None:
    if redis_connection is None:
        async with cache_redis_connection() as redis_conn:
            await cast(Awaitable[int], redis_conn.rpush(key, value))
    else:
        await cast(Awaitable[int], redis_connection.rpush(key, value))


async def exists(key: str, redis_connection: Optional[redis.Redis] = None) -> bool:
    if redis_connection is None:
        async with cache_redis_connection() as redis_conn:
            return (await cast(Awaitable[int], redis_conn.exists(key))) > 0
    else:
        return (await cast(Awaitable[int], redis_connection.exists(key))) > 0


async def hgetall(
    key: str, redis_connection: Optional[redis.Redis] = None
) -> dict[str, Any]:
    if redis_connection is None:
        async with cache_redis_connection() as redis_conn:
            return await cast(Awaitable[dict[str, Any]], redis_conn.hgetall(key))
    else:
        return await cast(Awaitable[dict[str, Any]], redis_connection.hgetall(key))


async def lpop(
    key: str, redis_connection: Optional[redis.Redis] = None
) -> Optional[Any]:
    if redis_connection is None:
        async with cache_redis_connection() as redis_conn:
            return await cast(Awaitable[Optional[Any]], redis_conn.lpop(key))
    else:
        return await cast(Awaitable[Optional[Any]], redis_connection.lpop(key))
