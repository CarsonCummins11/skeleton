import asyncio
import enum
import json
import logging
from typing import Optional
from uuid import uuid4

import asyncpg
import lib.redis
import lib.time
import redis.asyncio as redis
from lib import db
from pydantic import BaseModel, ValidationError

MAX_RETRY_COUNT = 3


class JobType(enum.Enum):
    # Add your job types here, e.g.:
    # SEND_EMAIL = "send_email"
    pass


class ExecutionSLO(enum.Enum):
    LEAKY_FAST = "leaky_fast"  # redis only — fastest, but failures are not retried
    DURABLE_FAST = "durable_fast"  # redis + SQL — fast and durable
    DURABLE_SLOW = "durable_slow"  # SQL only — slower, runs eventually


EXECUTION_CLASS_MAP: dict[JobType, ExecutionSLO] = {
    # Map each JobType to its SLO, e.g.:
    # JobType.SEND_EMAIL: ExecutionSLO.DURABLE_FAST,
}


class JobStatus(enum.Enum):
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    DLQ = 3


def _generate_job_id() -> str:
    return uuid4().hex


class _WorkqueueJob(BaseModel):
    job_id: str
    job_type: JobType
    status: JobStatus
    created_at: int
    payload: dict
    min_start_time: Optional[int] = None
    last_retry_at: Optional[int] = None
    retry_count: int = 0

    @classmethod
    async def load(
        cls,
        job_type: JobType,
        job_id: str,
        connection: asyncpg.Connection,
    ) -> Optional["_WorkqueueJob"]:
        row = await db.query_for_one(
            connection,
            """
            SELECT * FROM workqueue_jobs WHERE job_type = $1 AND job_id = $2
            """,
            job_type.value,
            job_id,
        )
        return (
            _WorkqueueJob(
                job_id=row["job_id"],
                job_type=JobType(row["job_type"]),
                status=JobStatus(row["status"]),
                created_at=row["created_at"],
                last_retry_at=row["last_retry_at"],
                retry_count=row["retry_count"],
                payload=row["payload"],
            )
            if row
            else None
        )

    async def _insert_into_database(self, connection: asyncpg.Connection):
        logging.info(
            f"Inserting job {self.job_id} into database for {self.job_type.name}"
        )
        await db.execute_query(
            connection,
            """
            INSERT INTO workqueue_jobs (job_id, job_type, status, created_at, last_retry_at, retry_count, payload)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            self.job_id,
            self.job_type.value,
            self.status.value,
            self.created_at,
            self.last_retry_at,
            self.retry_count,
            json.dumps(self.payload),
        )

    async def _insert_into_redis(self, redis_connection: Optional[redis.Redis] = None):
        logging.info(
            f"Inserting job {self.job_id} into Redis queue for {self.job_type.name}"
        )
        await lib.redis.rpush(
            f"queue-{self.job_type.name}", self.model_dump_json(), redis_connection
        )

    async def insert(
        self,
        redis_connection: Optional[redis.Redis] = None,
        connection: Optional[asyncpg.Connection] = None,
    ):
        coros = []
        if EXECUTION_CLASS_MAP[self.job_type] in [
            ExecutionSLO.LEAKY_FAST,
            ExecutionSLO.DURABLE_FAST,
        ]:
            coros.append(self._insert_into_redis(redis_connection))
        if EXECUTION_CLASS_MAP[self.job_type] != ExecutionSLO.LEAKY_FAST:
            assert connection, "Durable jobs must be inserted with a connection"
            coros.append(self._insert_into_database(connection))
        await asyncio.gather(*coros)


async def insert_job(
    job_type: JobType,
    payload: dict,
    redis_connection: Optional[redis.Redis] = None,
    connection: Optional[asyncpg.Connection] = None,
    job_id: Optional[str] = None,
) -> str:
    job_id = job_id or _generate_job_id()

    base_job_data = _WorkqueueJob(
        job_id=job_id,
        job_type=job_type,
        status=JobStatus.IN_PROGRESS,
        created_at=lib.time.usec_timestamp(),
        payload=payload,
    )

    await base_job_data.insert(redis_connection, connection)
    return job_id


async def get_job_status(
    job_type: JobType,
    job_id: str,
    connection: asyncpg.Connection,
) -> Optional[JobStatus]:
    job = await get_job(job_type, job_id, connection)
    return job.status if job else None


async def get_job(
    job_type: JobType,
    job_id: str,
    connection: asyncpg.Connection,
) -> Optional[_WorkqueueJob]:
    if EXECUTION_CLASS_MAP[job_type] == ExecutionSLO.LEAKY_FAST:
        raise ValueError("Leaky fast jobs do not provide any observability")
    return await _WorkqueueJob.load(job_type, job_id, connection)


async def _maybe_update_job_status(
    job_type: JobType,
    job_id: str,
    new_status: JobStatus,
    connection: asyncpg.Connection,
    force_for_redis_only: bool = False,
):
    if (
        EXECUTION_CLASS_MAP[job_type] == ExecutionSLO.LEAKY_FAST
        and not force_for_redis_only
    ):
        # Leaky fast jobs don't have status updates in the database
        return
    await db.execute_query(
        connection,
        """
        UPDATE workqueue_jobs
        SET status = $1
        WHERE job_type = $2 AND job_id = $3
        """,
        new_status.value,
        job_type.value,
        job_id,
    )


async def _maybe_increment_job_retry_count_in_db(
    job_type: JobType,
    job_id: str,
    connection: asyncpg.Connection,
):
    if EXECUTION_CLASS_MAP[job_type] == ExecutionSLO.LEAKY_FAST:
        # Leaky fast jobs don't have retry counts stored in the database
        return
    await db.execute_query(
        connection,
        """
        UPDATE workqueue_jobs
        SET retry_count = retry_count + 1, last_retry_at = $1
        WHERE job_type = $2 AND job_id = $3
        """,
        lib.time.usec_timestamp(),
        job_type.value,
        job_id,
    )


async def _maybe_get_job_from_redis(
    job_type: JobType,
    redis_connection: Optional[redis.Redis] = None,
) -> Optional[_WorkqueueJob]:
    job_data = await lib.redis.lpop(f"queue-{job_type.name}", redis_connection)
    if job_data:
        try:
            return _WorkqueueJob.model_validate_json(job_data)
        except ValidationError:
            logging.error(f"Invalid job data for {job_type.name}: {job_data}")
            return None
    return None


async def _maybe_get_job_from_db(
    job_type: JobType,
    connection: asyncpg.Connection,
) -> Optional[_WorkqueueJob]:
    if EXECUTION_CLASS_MAP[job_type] == ExecutionSLO.LEAKY_FAST:
        return None  # Leaky fast jobs are not stored in the database
    row = await db.query_for_one(
        connection,
        """
        SELECT * FROM workqueue_jobs
        WHERE job_type = $1 AND status = $2
        ORDER BY created_at ASC
        LIMIT 1
        """,
        job_type.value,
        JobStatus.NOT_STARTED.value,
    )
    if row:
        return _WorkqueueJob(
            job_id=row["job_id"],
            job_type=JobType(row["job_type"]),
            status=JobStatus(row["status"]),
            created_at=row["created_at"],
            last_retry_at=row["last_retry_at"],
            retry_count=row["retry_count"],
            payload=row["payload"],
        )
    return None


async def get_next_job(
    connection: Optional[asyncpg.Connection] = None,
) -> Optional[_WorkqueueJob]:
    for job_type in JobType:
        if EXECUTION_CLASS_MAP[job_type] == ExecutionSLO.DURABLE_SLOW:
            # Skip leaky fast jobs and durable fast jobs for this loop
            continue
        possible_next_job = await _maybe_get_job_from_redis(job_type)
        if possible_next_job:
            return possible_next_job
    async with await db.open_db_connection() as conn:
        for job_type in JobType:
            if EXECUTION_CLASS_MAP[job_type] == ExecutionSLO.LEAKY_FAST:
                # Skip leaky fast jobs for this loop
                continue
            possible_next_job = await _maybe_get_job_from_db(job_type, conn)
            if possible_next_job:
                return possible_next_job
    return None


async def mark_job_completed(
    job: _WorkqueueJob, connection: Optional[asyncpg.Connection] = None
):
    if EXECUTION_CLASS_MAP[job.job_type] == ExecutionSLO.LEAKY_FAST:
        # Leaky fast jobs don't have status updates in the database
        return
    if connection is None:
        async with await db.open_db_connection() as conn:
            await _maybe_update_job_status(
                job.job_type, job.job_id, JobStatus.COMPLETED, conn
            )
    else:
        await _maybe_update_job_status(
            job.job_type, job.job_id, JobStatus.COMPLETED, connection
        )


async def mark_job_in_progress(
    job: _WorkqueueJob, connection: Optional[asyncpg.Connection] = None
):
    if EXECUTION_CLASS_MAP[job.job_type] == ExecutionSLO.LEAKY_FAST:
        # Leaky fast jobs don't have status updates in the database
        return
    if connection is None:
        async with await db.open_db_connection() as conn:
            await _maybe_update_job_status(
                job.job_type, job.job_id, JobStatus.IN_PROGRESS, conn
            )
    else:
        await _maybe_update_job_status(
            job.job_type, job.job_id, JobStatus.IN_PROGRESS, connection
        )


async def _maybe_attach_job_error(
    job: _WorkqueueJob,
    error_message: str,
    connection: asyncpg.Connection,
):
    await db.execute_query(
        connection,
        """
        UPDATE workqueue_jobs
        SET error_message = $1
        WHERE job_type = $2 AND job_id = $3
        """,
        error_message,
        job.job_type.value,
        job.job_id,
    )


async def _kill_job(
    job: _WorkqueueJob,
    connection: asyncpg.Connection,
    error_message: Optional[str] = None,
):
    if EXECUTION_CLASS_MAP[job.job_type] == ExecutionSLO.LEAKY_FAST:
        # we want to report the failed job in the database, so we have to insert it first
        await job._insert_into_database(connection)
    """Move job to DLQ"""
    await _maybe_update_job_status(
        job.job_type, job.job_id, JobStatus.DLQ, connection, force_for_redis_only=True
    )
    if error_message:
        await _maybe_attach_job_error(job, error_message, connection)


async def handle_job_failure(job: _WorkqueueJob, error_message: Optional[str] = None):
    if job.retry_count == MAX_RETRY_COUNT:
        logging.error(f"Job {job.job_id} has reached max retry count, marking as DLQ")
        async with await db.open_db_connection() as conn:
            await _kill_job(job, conn, error_message)
        return
    if EXECUTION_CLASS_MAP[job.job_type] != ExecutionSLO.DURABLE_SLOW:
        # reinsert to redis with incremented retry count
        job.retry_count += 1
        job.last_retry_at = lib.time.usec_timestamp()
        job.status = JobStatus.NOT_STARTED
        await job._insert_into_redis()
    if EXECUTION_CLASS_MAP[job.job_type] == ExecutionSLO.LEAKY_FAST:
        return
    async with await db.open_db_connection() as conn:
        await _maybe_increment_job_retry_count_in_db(job.job_type, job.job_id, conn)
        await _maybe_update_job_status(
            job.job_type, job.job_id, JobStatus.NOT_STARTED, conn
        )
