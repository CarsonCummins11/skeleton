# Project Skeleton

A full-stack web application skeleton with a FastAPI backend, React frontend, background worker, and Terraform infrastructure for AWS deployment.

## Stack

| Layer | Technology |
|---|---|
| **API** | Python 3.13, FastAPI, asyncpg, uvicorn |
| **Database** | PostgreSQL |
| **Cache / PubSub** | Redis (two separate instances) |
| **Worker** | Python async work queue (Redis + Postgres backed) |
| **Frontend** | React 19, TypeScript, Vite, Bun, TanStack Router, TanStack Query, Tailwind CSS, shadcn/ui |
| **Infrastructure** | Terraform on AWS (ECS Fargate, RDS, ElastiCache, ALB, CloudFront, S3, Route53) |
| **CI/CD** | GitHub Actions |

---

## Local Development

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Bun](https://bun.sh/docs/installation) (JavaScript runtime)

### 1. Configure environment variables

Create `api/.env` (the file already exists in the repo for local dev — do not commit secrets):

```
DATABASE_URL=postgresql://fastapi:secret@db:5432/fastapi_db
CACHE_REDIS_URL=redis://default:secret@redis_cache:6379
PUBSUB_REDIS_URL=redis://default:secret@redis_pubsub:6379
SESSION_SECRET_KEY=<random-string>
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=dev
OPENAI_API_KEY=<your-openai-key>          # optional
LANGFUSE_PUBLIC_KEY=<your-langfuse-key>   # optional
LANGFUSE_SECRET_KEY=<your-langfuse-key>   # optional
```

### 2. Start the stack

```bash
docker compose up
```

This starts the API (`localhost:8000`), frontend (`localhost:5173`), worker, PostgreSQL, and both Redis instances.

On first boot in `ENVIRONMENT=dev` mode the API automatically applies `api/schema.sql` and seeds test data.

### Useful scripts

| Script | Purpose |
|---|---|
| `./restart_with_clear_db.sh` | Stop containers, wipe the DB and Redis volumes, restart |
| `./cycle_docker.sh` | Full Docker system prune + `docker compose up` |

### Running services individually (without Docker)

```bash
# API
cd api && uv run uvicorn route_server:app --reload --port 8000

# Worker
cd api && uv run python worker.py

# Frontend
cd frontend && bun install && bun run dev
```

---

## Project Structure

```
├── api/                  # FastAPI backend + worker
│   ├── lib/              # Shared utilities (db, redis, config, work queue)
│   ├── models/           # Pydantic models
│   ├── routes/           # Public API route handlers
│   ├── internal/         # Internal admin panel (Jinja2 + HTMX)
│   ├── schema.sql        # Database schema (auto-applied in dev)
│   ├── route_server.py   # FastAPI app entrypoint
│   └── worker.py         # Background job worker entrypoint
├── frontend/             # React + TypeScript SPA
│   └── src/
│       ├── routes/       # TanStack Router file-based routes
│       ├── lib/          # API client, utilities
│       └── components/   # UI components (shadcn/ui + custom)
├── tf/                   # Terraform infrastructure
│   ├── modules/
│   │   ├── service/      # ECS, RDS, Redis, ALB, networking
│   │   └── static_site/  # S3 + CloudFront + ACM + Route53
│   ├── main.tf
│   ├── variables.tf
│   └── backend.tf
├── .github/workflows/    # CI/CD pipelines
├── dockerfile.api
├── dockerfile.worker
├── dockerfile.frontend
└── docker-compose.yaml
```

---

## Environment Variables Reference

### `api/.env` (local dev)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `CACHE_REDIS_URL` | Yes | Redis cache connection string |
| `PUBSUB_REDIS_URL` | Yes | Redis pub/sub connection string |
| `SESSION_SECRET_KEY` | Yes | Secret key for signing session cookies |
| `FRONTEND_URL` | Yes | Allowed CORS origin (e.g. `http://localhost:5173`) |
| `ENVIRONMENT` | Yes | `dev` or `prod` |
| `OPENAI_API_KEY` | No | OpenAI API key |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse observability public key |
| `LANGFUSE_SECRET_KEY` | No | Langfuse observability secret key |

In production, `DATABASE_URL`, `CACHE_REDIS_URL`, `PUBSUB_REDIS_URL`, `FRONTEND_URL`, `ENVIRONMENT`, and `SESSION_SECRET_KEY` are all injected automatically by Terraform from the provisioned RDS and ElastiCache endpoints — you do not need to manage them manually.

### `frontend/src/env.ts`

Update the production API URL before deploying:

```ts
const PROD_API_URL = "https://api.your-app.com"; // <- replace this
```

---

## Deploying to AWS

### One-time setup

#### 1. Configure Terraform state backend

Edit `tf/backend.tf` and replace the placeholder values:

```hcl
terraform {
  backend "s3" {
    bucket = "your-app-tf-state"          # S3 bucket you create to hold state
    key    = "your-app/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Create the S3 bucket manually in your AWS account before running `terraform init`.

#### 2. Set your domain and credentials in Terraform variables

Edit `tf/variables.tf`:

```hcl
variable "domain_name" {
  default = "your-app.com"   # <- your domain, must be in Route53
}

variable "db_password" {
  default = "change-me"      # <- use a strong password
}
```

#### 3. Point your domain to Route53

The Terraform modules create Route53 hosted zones for the frontend (`your-app.com`) and API (`api.your-app.com`). After the first `terraform apply`, update your domain registrar's nameservers to match the Route53 NS records.

#### 4. Update the frontend production API URL

In `frontend/src/env.ts`, set `PROD_API_URL` to match `api.<your-app.com>`.

#### 5. Provision infrastructure

```bash
cd tf
terraform init
terraform apply
```

This creates: VPC, subnets, security groups, ALB, ECS clusters (API + Worker), RDS PostgreSQL, two ElastiCache Redis clusters, ECR repositories, S3 bucket, CloudFront distribution, ACM certificates, and Route53 records.

---

## GitHub Secrets

The following secrets must be set in your GitHub repository (`Settings → Secrets and variables → Actions`) before the CI/CD workflows will work.

### Required for all workflows

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key with ECS, ECR, S3, and Terraform permissions |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |

### Required for frontend deployment

| Secret | Description |
|---|---|
| `S3_BUCKET_NAME` | Name of the S3 bucket serving the frontend (created by Terraform as `<domain>-bucket`) |

> The `GITHUB_TOKEN` secret is provided automatically by GitHub Actions for the Terraform PR comment step — you do not need to create it.

---

## CI/CD Pipelines

Deployments trigger automatically on push to `main`:

| Workflow | Trigger path | Action |
|---|---|---|
| `deploy-backend.yml` | `api/**` | Builds `dockerfile.api`, pushes to ECR, force-deploys ECS API service |
| `deploy-worker.yml` | `api/**` | Builds `dockerfile.worker`, pushes to ECR, force-deploys ECS worker service |
| `deploy-frontend.yml` | `frontend/**` | Runs `bun build`, syncs `frontend/dist/` to S3 |
| `deploy-terraform.yml` | `tf/**` | On PR: posts `terraform plan` as a comment. On merge: runs `terraform apply` |

---

## Work Queue

The worker (`api/worker.py`) consumes jobs from the built-in work queue (`api/lib/wq.py`). Three execution SLOs are available:

| SLO | Storage | Behaviour |
|---|---|---|
| `LEAKY_FAST` | Redis only | Fastest; failures are not retried |
| `DURABLE_FAST` | Redis + Postgres | Fast pickup, durable persistence |
| `DURABLE_SLOW` | Postgres only | Guaranteed delivery, slower pickup |

To add a new job type:

1. Add an entry to `JobType` enum in `api/lib/wq.py`
2. Map it to an `ExecutionSLO` in `EXECUTION_CLASS_MAP`
3. Write a handler function and register it in `WORKMAP` in `api/worker.py`

---

## Customising the Skeleton

- **Domain model**: replace or extend `api/models/items.py` and `api/schema.sql`
- **API routes**: add routers under `api/routes/` and register them in `route_server.py`
- **Frontend routes**: add files under `frontend/src/routes/` — TanStack Router picks them up automatically
- **Internal admin panel**: Jinja2 templates live in `api/internal/templates/`; routes in `api/internal/routes.py`
- **ECS sizing**: tune CPU/memory/instance type in `tf/main.tf` or `tf/modules/service/variables.tf`
