import asyncio
import logging
import traceback

from lib import db, wq

# Map job types to their handler functions.
# Example:
#   from jobs.example import handle_example_job
#   WORKMAP = {wq.JobType.EXAMPLE_JOB: handle_example_job}
WORKMAP = {}


async def work_loop():
    await db.open_db_connection_pool()
    while True:
        try:
            job = await wq.get_next_job()
            if job:
                logging.info(f"Processing job {job.job_id} of type {job.job_type}")
                handler = WORKMAP.get(job.job_type)
                if handler:
                    try:
                        handler_coro = handler(**job.payload)
                        lock_coro = wq.mark_job_in_progress(job)
                        await asyncio.gather(handler_coro, lock_coro)
                        await wq.mark_job_completed(job)
                    except Exception as e:
                        logging.error(f"Error processing job {job.job_id}: {str(e)}")
                        await wq.handle_job_failure(job, str(e))
                else:
                    error_message = f"No handler found for job type {job.job_type}"
                    logging.error(error_message)
                    await wq.handle_job_failure(job, error_message)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Error in work loop: {str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(work_loop())
