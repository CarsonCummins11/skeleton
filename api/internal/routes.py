import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from lib import db, wq
from lib.time import format_timestamp
from models.users import User, get_password_hash

from .auth import (
    clear_intranet_session,
    create_intranet_session,
    get_current_intranet_user,
    require_intranet_auth,
    verify_intranet_user,
)

router = APIRouter()

# Setup Jinja2 environment
template_dir = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"])
)


def format_json(data):
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            return data
    else:
        return json.dumps(data, indent=2)


jinja_env.filters["format_timestamp"] = format_timestamp
jinja_env.filters["format_json"] = format_json

# Static files will be mounted at the main app level


def render_template(
    template_name: str, request: Optional[Request] = None, **context
) -> str:
    """Render a Jinja template with the given context"""
    template = jinja_env.get_template(template_name)
    if request:
        context["request"] = request
    return template.render(**context)


@router.get("/", response_class=HTMLResponse)
async def intranet_home(request: Request):
    """Show intranet user page"""
    user = await require_intranet_auth(request)
    return HTMLResponse(
        render_template("intranet_user.html", request=request, user=user)
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page"""
    user = await get_current_intranet_user(request)
    if user:
        return RedirectResponse(url="/internal/")

    return HTMLResponse(render_template("login.html", request=request))


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = verify_intranet_user(username, password)
    if user:
        create_intranet_session(request, username)
        return RedirectResponse(url="/internal/", status_code=303)
    else:
        return HTMLResponse(
            render_template(
                "login.html", request=request, error="Invalid username or password"
            )
        )


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Handle logout"""
    clear_intranet_session(request)
    return RedirectResponse(url="/internal/login", status_code=303)


@router.get("/create-user", response_class=HTMLResponse)
async def create_user_page(request: Request):
    """Show create user page"""
    user = await require_intranet_auth(request)
    return HTMLResponse(render_template("create_user.html", request=request, user=user))


@router.post("/create-user", response_class=HTMLResponse)
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    profile_image_url: str = Form(...),
):
    user = await require_intranet_auth(request)

    try:
        async with await db.open_db_connection() as connection:
            # Check if user already exists
            existing_user = await User.load_from_username(connection, username)
            if existing_user:
                return HTMLResponse(
                    render_template(
                        "create_user.html",
                        request=request,
                        user=user,
                        error=f"User with username '{username}' already exists.",
                    )
                )

            # Create new user
            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                hashed_password=hashed_password,
                full_name=full_name,
                profile_image_url=profile_image_url,
            )
            await new_user.create(connection)

            user_info = {
                "username": username,
                "full_name": full_name,
                "profile_image_url": profile_image_url,
            }

            return HTMLResponse(
                render_template(
                    "create_user.html",
                    request=request,
                    user=user,
                    success=f"User '{username}' created successfully!",
                    user_info=user_info,
                )
            )
    except Exception as e:
        return HTMLResponse(
            render_template(
                "create_user.html",
                request=request,
                user=user,
                error=f"Error creating user: {str(e)}",
            )
        )


@router.get("/query", response_class=HTMLResponse)
async def query_dashboard(request: Request, query: str = ""):
    """Query database page"""
    user = await require_intranet_auth(request)

    column_headers = None
    rows = None

    if query:
        try:
            async with await db.open_db_connection() as connection:
                fetched = await connection.fetch(query)
                if fetched:
                    column_headers = list(fetched[0].keys())
                    rows = [list(row.values()) for row in fetched]
                else:
                    column_headers = []
                    rows = []
        except Exception as e:
            return HTMLResponse(
                render_template(
                    "query.html",
                    request=request,
                    user=user,
                    query=query,
                    error=f"Query error: {str(e)}",
                )
            )
    return HTMLResponse(
        render_template(
            "query.html",
            request=request,
            user=user,
            query=query,
            column_headers=column_headers,
            rows=rows,
        )
    )


@router.post("/query/reset-database", response_class=HTMLResponse)
async def reset_database(request: Request):
    """Reset database by dropping all tables and rerunning applets.sql"""
    user = await require_intranet_auth(request)

    try:
        async with await db.open_db_connection() as connection:
            schema_sql_path = Path(__file__).parent.parent / "schema.sql"
            with open(schema_sql_path, "r") as f:
                schema_sql = f.read()

            await connection.execute(
                "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
            )
            await connection.execute(schema_sql)

        return HTMLResponse(
            render_template(
                "query.html",
                request=request,
                user=user,
                query="",
                success="Database successfully reset and schema.sql rerun.",
            )
        )

    except Exception as e:
        return HTMLResponse(
            render_template(
                "query.html",
                request=request,
                user=user,
                query="",
                error=f"Database reset error: {str(e)}",
            )
        )


# WQ (Work Queue) Management Routes
@router.get("/wq", response_class=HTMLResponse)
async def wq_dashboard(request: Request):
    """Show WQ dashboard with job statistics by queue"""
    user = await require_intranet_auth(request)

    async with await db.open_db_connection() as conn:
        # Get job statistics by queue
        stats_query = """
        SELECT 
            job_type,
            status,
            COUNT(*) as count
        FROM workqueue_jobs 
        GROUP BY job_type, status
        ORDER BY job_type, status
        """
        stats_result = await db.query_for_all(conn, stats_query)

        # Organize stats by queue and status
        queue_stats = {
            job_t.name.lower(): {
                "not_started": 0,
                "in_progress": 0,
                "completed": 0,
                "dlq": 0,
            }
            for job_t in wq.JobType
        }
        for row in stats_result:
            job_type = row["job_type"].lower()
            count = row["count"]
            status_name = wq.JobStatus(row["status"]).name.lower()
            queue_stats[job_type][status_name] = count

    return HTMLResponse(
        render_template(
            "wq_dashboard.html", request=request, user=user, queue_stats=queue_stats
        )
    )


@router.get("/wq/queue/{job_type}", response_class=HTMLResponse)
async def wq_queue_jobs(request: Request, job_type: str, status: Optional[str] = None):
    """Show jobs for a specific queue with optional status filter"""
    user = await require_intranet_auth(request)

    async with await db.open_db_connection() as conn:
        # Build query with optional status filter
        if status:
            query = """
                SELECT * FROM workqueue_jobs
                WHERE job_type = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT 100
                """
            jobs_result = await db.query_for_all(
                conn, query, job_type, wq.JobStatus[status.upper()].value
            )
        else:
            query = """
            SELECT * FROM workqueue_jobs
            WHERE job_type = $1
            ORDER BY created_at DESC
            LIMIT 100
            """
            jobs_result = await db.query_for_all(conn, query, job_type)

    return HTMLResponse(
        render_template(
            "wq_queue.html",
            request=request,
            user=user,
            job_type=job_type,
            status=status,
            jobs=jobs_result,
        )
    )


@router.get("/wq/job/{job_type}/{job_id}", response_class=HTMLResponse)
async def wq_job_detail(request: Request, job_type: str, job_id: str):
    """Show detailed information about a specific job"""
    user = await require_intranet_auth(request)

    async with await db.open_db_connection() as conn:
        query = """
        SELECT * FROM workqueue_jobs
        WHERE job_type = $1 AND job_id = $2
        """
        job_result = await db.query_for_one(conn, query, job_type, job_id)

        if not job_result:
            return HTMLResponse(
                render_template(
                    "wq_job_detail.html",
                    request=request,
                    user=user,
                    job=None,
                    error="Job not found",
                )
            )

    return HTMLResponse(
        render_template(
            "wq_job_detail.html", request=request, user=user, job=job_result
        )
    )


@router.post("/wq/job/{job_type}/{job_id}/revive", response_class=HTMLResponse)
async def wq_revive_job(request: Request, job_type: str, job_id: str):
    """Revive a job from DLQ by resetting its status to NOT_STARTED"""
    user = await require_intranet_auth(request)

    try:
        # Get the job
        job_type_enum = wq.JobType(job_type)
        async with await db.open_db_connection() as conn:
            job = await wq.get_job(job_type_enum, job_id, conn)

            if not job:
                return HTMLResponse(
                    render_template(
                        "wq_job_detail.html",
                        request=request,
                        user=user,
                        job=None,
                        error="Job not found",
                    )
                )

            if job.status != wq.JobStatus.DLQ:
                return HTMLResponse(
                    render_template(
                        "wq_job_detail.html",
                        request=request,
                        user=user,
                        job=job.__dict__,
                        error="Only DLQ jobs can be revived",
                    )
                )

            # Reset job status to NOT_STARTED and retry count to 0
            await db.execute_query(
                conn,
                """
                UPDATE workqueue_jobs
                SET status = $1, retry_count = 0, error_message = NULL
                WHERE job_type = $2 AND job_id = $3
                """,
                wq.JobStatus.NOT_STARTED.value,
                job_type,
                job_id,
            )

            if wq.EXECUTION_CLASS_MAP[job_type_enum] != wq.ExecutionSLO.DURABLE_SLOW:
                job.status = wq.JobStatus.NOT_STARTED
                job.retry_count = 0
                await job._insert_into_redis()

            return RedirectResponse(
                url=f"/internal/wq/job/{job_type}/{job_id}?success=Job revived successfully",
                status_code=303,
            )

    except Exception as e:
        return HTMLResponse(
            render_template(
                "wq_job_detail.html",
                request=request,
                user=user,
                job=None,
                error=f"Error reviving job: {str(e)}",
            )
        )


@router.post("/wq/job/{job_type}/{job_id}/delete", response_class=HTMLResponse)
async def wq_delete_job(request: Request, job_type: str, job_id: str):
    """Delete a job from the work queue"""
    user = await require_intranet_auth(request)

    try:
        async with await db.open_db_connection() as conn:
            # Check if job exists
            job_result = await db.query_for_one(
                conn,
                "SELECT * FROM workqueue_jobs WHERE job_type = $1 AND job_id = $2",
                job_type,
                job_id,
            )

            if not job_result:
                return HTMLResponse(
                    render_template(
                        "wq_job_detail.html",
                        request=request,
                        user=user,
                        job=None,
                        error="Job not found",
                    )
                )

            # Delete the job
            await db.execute_query(
                conn,
                "DELETE FROM workqueue_jobs WHERE job_type = $1 AND job_id = $2",
                job_type,
                job_id,
            )

            return RedirectResponse(
                url=f"/internal/wq/queue/{job_type}?success=Job deleted successfully",
                status_code=303,
            )

    except Exception as e:
        return HTMLResponse(
            render_template(
                "wq_job_detail.html",
                request=request,
                user=user,
                job=None,
                error=f"Error deleting job: {str(e)}",
            )
        )
