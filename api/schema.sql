-- Users table
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(32) PRIMARY KEY,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    profile_image_url VARCHAR(255) NOT NULL
);

-- Example items table — replace or extend with your domain model
CREATE TABLE IF NOT EXISTS items (
    id CHAR(12) PRIMARY KEY,
    owner_username VARCHAR(32) NOT NULL REFERENCES users(username),
    title TEXT NOT NULL,
    description TEXT,
    created_at BIGINT NOT NULL
);

-- Work queue table (used by worker.py)
CREATE TABLE IF NOT EXISTS workqueue_jobs (
    job_id VARCHAR(32),
    job_type TEXT NOT NULL,
    status INTEGER NOT NULL,
    created_at BIGINT NOT NULL,
    last_retry_at BIGINT,
    retry_count INTEGER NOT NULL,
    payload JSON NOT NULL,
    error_message TEXT,
    PRIMARY KEY (job_type, job_id)
);
