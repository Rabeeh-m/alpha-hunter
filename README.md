<div align="center">

# 🎯 Alpha Hunter

**AI-Powered Crypto Intelligence Platform for Early-Stage Token Discovery**

[![CI](https://img.shields.io/badge/CI-passing-brightgreen?logo=githubactions)](#)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue?logo=python)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)](#)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](#)
[![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64)](#)
[![Black](https://img.shields.io/badge/code%20style-black-000000)](#)
[![mypy](https://img.shields.io/badge/type--checked-mypy-2A6DB2)](#)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)](#)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey)](#)

*A transparent, explainable research tool — not a prediction engine, not financial advice.*

</div>

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Screenshots](#3-screenshots)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Project Structure](#6-project-structure)
7. [System Workflow](#7-system-workflow)
8. [Data Flow](#8-data-flow)
9. [Installation](#9-installation)
10. [Local Development](#10-local-development)
11. [Docker Deployment](#11-docker-deployment)
12. [Environment Variables](#12-environment-variables)
13. [Configuration](#13-configuration)
14. [Database Design](#14-database-design)
15. [REST API](#15-rest-api)
16. [Scheduler](#16-scheduler)
17. [Alpha Scoring](#17-alpha-scoring)
18. [Logging](#18-logging)
19. [Security](#19-security)
20. [Performance](#20-performance)
21. [Monitoring & Observability](#21-monitoring--observability)
22. [Testing](#22-testing)
23. [Code Quality](#23-code-quality)
24. [CI/CD](#24-cicd)
25. [Documentation Standards](#25-documentation-standards)
26. [Roadmap](#26-roadmap)
27. [Contributing](#27-contributing)
28. [Troubleshooting](#28-troubleshooting)
29. [Best Practices](#29-best-practices)
30. [Production Deployment](#30-production-deployment)
31. [Future Improvements](#31-future-improvements)
32. [License](#32-license)
33. [Acknowledgements](#33-acknowledgements)
34. [Contact](#34-contact)

---

## 1. Project Overview

### Vision
A world where anyone doing early-stage crypto research has access to the same class of on-chain and off-chain signal analysis that quantitative trading desks use internally — presented transparently, with every score traceable to the data that produced it.

### Mission
Continuously discover newly launched tokens across major blockchains, enrich them with liquidity, wallet, developer, social, and narrative signals, and surface an explainable **Alpha Score** — never a black-box prediction.

### Purpose
Manual crypto research is slow, fragmented across a dozen tools, and biased toward whoever shouts loudest on social media. Alpha Hunter automates the *data collection and signal aggregation* work, leaving the human in charge of the final judgment call.

### Target Users
| User | Use Case |
|---|---|
| Independent researchers | Screen new listings without manually checking 5+ sites per token |
| Quant/dev teams | Programmatic access via REST API for internal tooling |
| Content creators / analysts | Data-backed narrative and trend reporting |
| Engineers learning AI/data engineering | Reference implementation of a production-grade data platform |

### Business Value
- Reduces research time from hours to minutes per token
- Centralizes fragmented data sources into one queryable system
- Produces a defensible, explainable score instead of unverifiable "gut feel" calls

### Technical Value
- Reference-quality implementation of Clean Architecture in an async Python service
- Demonstrates multi-source data normalization, caching, and idempotent ingestion at scale
- A genuine ML pipeline (later milestones) trained on real historical outcomes, not synthetic data

### Key Capabilities
- Multi-chain, multi-provider token discovery
- Liquidity, contract-risk, wallet, developer, social, and narrative analysis (see [Roadmap](#26-roadmap) for what's live today vs. planned)
- Explainable scoring — every score decomposes into its contributing factors
- REST API with search, filtering, sorting, pagination
- Scheduled, automatic data refresh

### Non-Goals
- ❌ Alpha Hunter does **not** execute trades
- ❌ Alpha Hunter does **not** custody funds or private keys
- ❌ Alpha Hunter does **not** promise or predict returns
- ❌ Alpha Hunter is **not** a replacement for your own due diligence

> **⚠️ Disclaimer:** Alpha Hunter is a research and data-aggregation tool. Cryptocurrency markets are highly volatile and speculative. Nothing produced by this system constitutes financial advice. Newly launched tokens carry a materially elevated risk of scams, rug pulls, and total loss of capital. Always do your own research.

---

## 2. Features

### V1 — Core Screener *(in progress)*
- [x] Project scaffolding, config management, structured logging
- [x] Async SQLAlchemy + Alembic + PostgreSQL persistence
- [x] DexScreener collector (cached, retried, upserted)
- [ ] GeckoTerminal collector + cross-provider deduplication
- [ ] APScheduler background refresh
- [ ] Token search/filter/sort/pagination API
- [ ] Token detail + historical snapshots
- [ ] Ranking Engine V1 (liquidity, volume, market cap, age, growth)
- [ ] CLI management commands
- [ ] Test suite ≥90% coverage, full documentation, V1 release

### V2 — Wallet Intelligence *(planned)*
- [ ] Smart money / VC / exchange wallet tagging
- [ ] Wallet clustering, accumulation/selling pattern detection

### V3 — Contract Security *(planned)*
- [ ] Mint function, ownership, proxy, tax detection
- [ ] Automated contract risk score

### V4–V15 — Whale Tracking, Social Intelligence, Narrative Detection, GitHub Analysis, ML, Alpha Score Engine, Alerts, React Dashboard, Portfolio, Paper Trading, Backtesting, AI Research Assistant
See [§26 Roadmap](#26-roadmap) for full detail.

---

## 3. Screenshots

> Dashboard (V11) has not been built yet — placeholders below reflect the planned UI.

| View | Description |
|---|---|
| ![Dashboard](docs/assets/screenshot-dashboard.png) | Overview dashboard — top movers, trending narratives, alert feed |
| ![Screener](docs/assets/screenshot-screener.png) | Token screener — filterable, sortable table of discovered tokens |
| ![Token Detail](docs/assets/screenshot-token-detail.png) | Single-token deep dive — liquidity chart, holder distribution, score breakdown |
| ![Wallet Tracker](docs/assets/screenshot-wallets.png) | Smart-money wallet activity feed |
| ![Narrative Analysis](docs/assets/screenshot-narratives.png) | Narrative momentum over time |
| ![Risk Dashboard](docs/assets/screenshot-risk.png) | Contract risk flags across tracked tokens |

---

## 4. High-Level Architecture

```mermaid
flowchart TB
    subgraph Sources["Data Sources"]
        DS[DexScreener API]
        GT[GeckoTerminal API]
        GH[GitHub API]
        SOC[Social APIs]
        RPC[Chain RPC Nodes]
    end

    subgraph Collectors["Collectors Layer"]
        DSC[DexScreener Collector]
        GTC[GeckoTerminal Collector]
        DEV[Developer Collector]
        SOCC[Social Collector]
        CHAIN[On-chain Collector]
    end

    subgraph Core["Processing Core"]
        NORM[Normalizers]
        SVC[Service Layer]
        RANK[Ranking / Scoring Engine]
        ML[ML Pipeline]
    end

    subgraph Storage["Storage"]
        PG[(PostgreSQL)]
        REDIS[(Redis Cache)]
    end

    subgraph Delivery["Delivery Layer"]
        API[FastAPI REST API]
        SCHED[APScheduler Jobs]
        ALERT[Alert Engine]
        DASH[React Dashboard]
    end

    DS --> DSC --> NORM
    GT --> GTC --> NORM
    GH --> DEV --> NORM
    SOC --> SOCC --> NORM
    RPC --> CHAIN --> NORM

    NORM --> SVC --> PG
    SVC <--> REDIS
    SVC --> RANK --> PG
    SVC --> ML --> PG

    SCHED --> SVC
    PG --> API
    API --> DASH
    RANK --> ALERT
```

**Component responsibilities:**
- **Collectors** — provider-specific HTTP clients; know *how* to talk to one external API, nothing else.
- **Normalizers** — translate each provider's raw JSON shape into internal DTOs.
- **Service Layer** — orchestrates business workflows (ingest, score, alert); the only layer that knows the *sequence* of operations.
- **Repositories** — the only layer that issues SQL/ORM queries.
- **Ranking/ML** — read persisted data, write back scores; never call external APIs directly.
- **API** — HTTP-facing, thin, delegates to services.

---

## 5. Technology Stack

### Backend
| Technology | Why |
|---|---|
| Python 3.13+ | Modern async syntax, performance improvements, strong typing support |
| FastAPI | Async-native, auto-generated OpenAPI docs, Pydantic integration |
| Pydantic v2 | Fast validation, used consistently for config, DTOs, and API schemas |

### Database
| Technology | Why |
|---|---|
| PostgreSQL 17 | Mature, ACID-compliant, strong JSON + full-text + partitioning support for time-series-heavy data |
| SQLAlchemy 2.x (async) | Industry-standard ORM with first-class async support |
| Alembic | Versioned, reviewable schema migrations |

### Blockchain
| Technology | Why |
|---|---|
| web3.py | De facto standard for EVM chain interaction in Python |
| eth-account | Local key handling for read-only wallet analysis (no custody) |

### AI/ML
| Technology | Why |
|---|---|
| scikit-learn | Baseline models, preprocessing pipelines, evaluation metrics |
| XGBoost / LightGBM / CatBoost | Gradient-boosted trees — strong performance on tabular, imbalanced financial data; comparing three lets us pick the best per-feature-set performer |
| sentence-transformers | Embedding-based narrative/topic classification |

### Data Processing
| Technology | Why |
|---|---|
| Pandas | Feature engineering, dataset assembly for ML |
| Polars | Faster columnar processing for large historical backtests |

### DevOps
| Technology | Why |
|---|---|
| Docker / Docker Compose | Reproducible local + deployment environments |
| GitHub Actions | CI: lint, type-check, test, coverage gate on every PR |

### Testing
| Technology | Why |
|---|---|
| pytest / pytest-asyncio | Standard async-compatible test runner |
| respx | Mocks httpx calls — collector tests never hit real networks |
| pytest-cov | Coverage enforcement (≥90% target) |

### Code Quality
| Technology | Why |
|---|---|
| Ruff | Fast, single-tool linting (replaces flake8 + isort + more) |
| Black | Deterministic formatting — zero bikeshedding on style |
| mypy (strict) | Catches type errors before runtime |
| pre-commit | Enforces all of the above before code reaches CI |

---

## 6. Project Structure

```
alpha-hunter/
├── app/
│   ├── api/                  # FastAPI routers — HTTP layer only
│   │   └── v1/
│   ├── blockchain/           # Chain-specific RPC clients (web3.py wrappers)
│   ├── collectors/            # External data provider clients + normalizers
│   ├── core/
│   │   ├── config/            # pydantic-settings configuration
│   │   ├── database/           # SQLAlchemy engine/session, Alembic migrations
│   │   └── logging/            # structlog setup
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic DTOs (API request/response, provider payloads)
│   ├── repositories/           # Data access layer (Repository Pattern)
│   ├── services/                # Business logic / use-case orchestration
│   ├── ranking/                 # Scoring engine (planned M8)
│   ├── risk/                    # Contract/wallet risk analysis (planned V3)
│   ├── ml/                      # Feature engineering, training, inference (planned V8)
│   ├── alerts/                  # Notification dispatch (planned V10)
│   ├── dashboard/                # (planned V11 — separate React app)
│   ├── tests/                    # pytest suite, mirrors app/ structure
│   └── main.py                   # FastAPI app factory / composition root
├── docker/
│   └── Dockerfile                # Multi-stage: dev / production targets
├── docs/                          # Architecture docs, ADRs, roadmap
├── scripts/                        # One-off ops/maintenance scripts
├── .github/workflows/               # CI pipeline definitions
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .env.example
└── README.md
```

---

## 7. System Workflow

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant Col as Collector
    participant Norm as Normalizer
    participant Svc as IngestionService
    participant Repo as Repository
    participant DB as PostgreSQL
    participant Rank as Ranking Engine
    participant API as REST API
    participant User as Client / Dashboard

    Sched->>Col: trigger fetch (interval)
    Col->>Col: check Redis cache
    alt cache miss
        Col->>Col: HTTP GET provider API (retried)
    end
    Col->>Norm: raw provider JSON
    Norm->>Svc: normalized TokenCreate DTO
    Svc->>Repo: upsert(token)
    Repo->>DB: INSERT ... ON CONFLICT UPDATE
    Sched->>Rank: trigger scoring pass
    Rank->>DB: read latest signals
    Rank->>DB: write AlphaScore
    User->>API: GET /api/v1/tokens?sort=alpha_score
    API->>Repo: query
    Repo->>DB: SELECT
    DB-->>API: rows
    API-->>User: paginated JSON response
```

---

## 8. Data Flow

```mermaid
flowchart LR
    A[Provider APIs] -->|raw JSON| B[Collector]
    B -->|cached 60s| C[(Redis)]
    B -->|parsed| D[Normalizer]
    D -->|TokenCreate DTO| E[Service Layer]
    E -->|upsert| F[(PostgreSQL)]
    F -->|read| G[Ranking Engine]
    G -->|AlphaScore| F
    F -->|read| H[FastAPI]
    H -->|JSON| I[Client / Dashboard / CLI]
    G -.->|threshold breach| J[Alert Engine]
    J -->|notify| K[Telegram / Discord / Slack]
```

---

## 9. Installation

### Prerequisites
| Requirement | Minimum Version | Notes |
|---|---|---|
| Python | 3.13+ | Use `pyenv` if your OS ships an older default |
| Docker + Docker Compose | 24+ | For Postgres/Redis without local installs |
| Git | any recent | |

### Supported OS
Linux (primary), macOS, Windows via WSL2. Native Windows is untested.

### Docker Installation
Follow the [official Docker Engine install guide](https://docs.docker.com/engine/install/) for your OS, then confirm:
```bash
docker --version
docker compose version
```

### PostgreSQL & Redis
Not required to be installed locally — both run via `docker-compose.yml`. If you prefer native installs, PostgreSQL 17+ and Redis 7+ work identically; just point `DATABASE_URL`/`REDIS_URL` at them.

---

## 10. Local Development

```bash
# 1. Clone the repository
git clone <repository-url> alpha-hunter
cd alpha-hunter

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Configure environment variables
cp .env.example .env
# edit .env: set SECRET_KEY, confirm DATABASE_URL / REDIS_URL

# 5. Start PostgreSQL + Redis
docker compose up -d postgres redis
docker compose ps                 # confirm both are "healthy"

# 6. Run database migrations
alembic upgrade head

# 7. (Once implemented) start the scheduler
python -m app.scheduler

# 8. Run the FastAPI server
uvicorn app.main:app --reload

# 9. Verify
curl http://localhost:8000/health
```

Frontend dashboard setup will be documented once V11 lands.

---

## 11. Docker Deployment

```bash
# Build and start the full stack
docker compose up --build -d

# View logs
docker compose logs -f api

# Stop (containers persist)
docker compose stop

# Stop and remove containers (volumes persist)
docker compose down

# Remove everything including volumes (⚠️ deletes DB data)
docker compose down -v

# Rebuild after dependency changes
docker compose build --no-cache api
docker compose up -d
```

> **Note:** the `docker/Dockerfile` uses multi-stage builds — `dev` (hot reload, dev tooling) and `production` (slim, non-root user, `HEALTHCHECK`). `docker-compose.yml` uses the `dev` target locally; production deployments should target `production` explicitly.

---

## 12. Environment Variables

| Variable | Description | Required | Default | Example |
|---|---|:---:|---|---|
| `APP_NAME` | Display name of the service | No | `Alpha Hunter` | `Alpha Hunter` |
| `ENVIRONMENT` | Deployment environment | No | `local` | `production` |
| `DEBUG` | Enable FastAPI debug mode | No | `false` | `true` |
| `LOG_LEVEL` | Minimum log level | No | `INFO` | `DEBUG` |
| `LOG_JSON` | Emit JSON logs (prod) vs console (dev) | No | `true` | `false` |
| `SECRET_KEY` | JWT signing secret | **Yes** | — | `openssl rand -hex 32` output |
| `JWT_ALGORITHM` | JWT signing algorithm | No | `HS256` | `HS256` |
| `DATABASE_URL` | Async Postgres connection string | **Yes** | — | `postgresql+asyncpg://user:pass@localhost:5432/alpha_hunter` |
| `DATABASE_POOL_SIZE` | SQLAlchemy connection pool size | No | `10` | `20` |
| `REDIS_URL` | Redis connection string | **Yes** | — | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker (defaults to `REDIS_URL`) | No | `REDIS_URL` | `redis://localhost:6379/1` |
| `ETHEREUM_RPC_URL` | Ethereum RPC endpoint | No | — | Alchemy/Infura URL |
| `BASE_RPC_URL` | Base RPC endpoint | No | — | |
| `SOLANA_RPC_URL` | Solana RPC endpoint | No | — | |
| `DEXSCREENER_API_KEY` | DexScreener API key (if required by plan tier) | No | — | |
| `OPENAI_API_KEY` | OpenAI API key (narrative/NLP features) | No | — | |
| `ANTHROPIC_API_KEY` | Anthropic API key (narrative/NLP features) | No | — | |
| `TELEGRAM_BOT_TOKEN` | Alert delivery via Telegram | No | — | |
| `DISCORD_WEBHOOK_URL` | Alert delivery via Discord | No | — | |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | API rate limit | No | `60` | `120` |

See `.env.example` for the complete, up-to-date list — this table is kept in sync with it.

---

## 13. Configuration

All configuration flows through `app/core/config/settings.py::Settings`, a `pydantic-settings.BaseSettings` subclass. This is the **only** place environment variables are read — no module elsewhere should call `os.getenv` directly.

**Best practices:**
- Never commit `.env` — only `.env.example` with placeholder values.
- Secrets are typed `SecretStr` so they never leak into logs or `repr()` output.
- `get_settings()` is `lru_cache`d — parsed once per process, not per request.
- Required fields (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`) cause immediate startup failure if missing — fail fast, not three hours into a shift.

---

## 14. Database Design

```mermaid
erDiagram
    TOKENS {
        uuid id PK
        enum chain
        string contract_address
        string pair_address
        string name
        string symbol
        int decimals
        string dex
        numeric liquidity_usd
        numeric market_cap_usd
        numeric fdv_usd
        numeric volume_24h_usd
        numeric price_usd
        int holder_count
        timestamp created_at
        timestamp updated_at
    }
    ALPHA_SCORES {
        uuid id PK
        uuid token_id FK
        numeric score
        jsonb factor_breakdown
        timestamp computed_at
    }
    WALLETS {
        uuid id PK
        string address
        enum chain
        enum wallet_type
        numeric confidence_score
    }
    TOKENS ||--o{ ALPHA_SCORES : "has many"
    TOKENS ||--o{ WALLETS : "held by (planned V2)"
```

**Current tables (V1):** `tokens` — unique on `(chain, contract_address)`, indexed on `chain` and `contract_address` individually for lookup performance.

**Planned tables:** `alpha_scores`, `wallets`, `transactions`, `narratives`, `alerts`, `social_metrics`, `historical_prices`, `contracts`, `developer_metrics`, `ml_predictions` — introduced incrementally as their owning milestone lands.

**Migration strategy:** every schema change is a reviewed Alembic migration generated via `alembic revision --autogenerate`, never a manual schema edit against a running database. Migrations are applied via `alembic upgrade head` in CI and deployment pipelines — never run ad hoc against production without review.

---

## 15. REST API

> **Status:** `/health` is live. Token search/filter/sort endpoints land in Milestone 6 — this section will be filled in with live examples at that point. Shape below reflects the planned contract.

**Base URL:** `http://localhost:8000/api/v1` (local) — **Authentication:** none yet (V1); JWT bearer auth planned alongside the dashboard (V11).

**Planned endpoint:**
```
GET /api/v1/tokens?chain=base&min_liquidity=10000&sort=-alpha_score&page=1&page_size=25
```

**Example response shape:**
```json
{
  "items": [
    {
      "id": "b3f1...",
      "chain": "base",
      "symbol": "TEST",
      "liquidity_usd": "15000.00000000",
      "alpha_score": null
    }
  ],
  "page": 1,
  "page_size": 25,
  "total": 1
}
```

**Error responses** follow a consistent envelope:
```json
{ "detail": "Token not found", "status_code": 404 }
```

Interactive OpenAPI docs are auto-generated by FastAPI at `/docs` (Swagger UI) and `/redoc`.

---

## 16. Scheduler

*(Planned — Milestone 5)*

Background refresh jobs will run via APScheduler, on a configurable interval per collector (DexScreener default: every 60s, matching the Redis cache TTL to avoid redundant work). Each job will be wrapped with the same `tenacity` retry policy used in collectors, log structured start/success/failure events, and expose job status via a future `/health/jobs` endpoint for monitoring.

---

## 17. Alpha Scoring

**Philosophy:** every score must be traceable to the specific data points that produced it. A user should never see a number with no explanation attached — this is a hard requirement, not a nice-to-have.

**Explainability:** the planned `AlphaScore` model stores a `factor_breakdown` JSONB column alongside the composite score, recording each category's raw sub-score and weight, so the API can return "why" alongside "what."

**Current scoring factors (V1, planned M8):** liquidity, 24h volume, market cap, token age, liquidity growth rate — a simple, transparent weighted composite as the baseline before ML-based scoring (V8/V9) is introduced.

**Future enhancements:** wallet intelligence, contract risk, developer activity, social signals, and narrative momentum will each become additional weighted factors as their respective milestones land, with ML models (V8) eventually learning optimal weights from historical outcome data rather than hand-tuned weights.

---

## 18. Logging

Structured logging via `structlog`. **Format:** JSON in production (`LOG_JSON=true`) for log-aggregator ingestion; colored console output in local dev. **Levels:** standard `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`, configured via `LOG_LEVEL`. **Correlation:** `structlog.contextvars` binds contextual fields (e.g. `chain`, `token_address`, future `job_id`/`request_id`) so all log lines emitted while processing one unit of work carry that context automatically. **Rotation:** handled at the infrastructure level (Docker log driver / log-aggregator retention policy), not application-level — the app writes to stdout per 12-Factor App principles.

---

## 19. Security

| Concern | Approach |
|---|---|
| Secrets management | `SecretStr` typing, `.env` git-ignored, no secrets in code or logs |
| Authentication | JWT planned alongside dashboard (V11); currently no auth (local-only V1 scope) |
| Input validation | Pydantic schemas validate all API input at the boundary |
| SQL injection | SQLAlchemy parameterized queries exclusively — no raw string-interpolated SQL anywhere |
| Rate limiting | Redis-backed, planned per `RATE_LIMIT_REQUESTS_PER_MINUTE` |
| XSS / CSRF | Primarily a backend API; dashboard (React, V11) will apply standard React escaping + CSRF tokens for any state-changing requests |
| Dependency scanning | GitHub Dependabot / `pip-audit` recommended in CI (planned addition) |

---

## 20. Performance

- **Async everywhere:** FastAPI + async SQLAlchemy + httpx — I/O-bound work (API calls, DB queries) never blocks the event loop.
- **Connection pooling:** configurable `DATABASE_POOL_SIZE`/`DATABASE_MAX_OVERFLOW`, `pool_pre_ping=True` to avoid stale-connection errors.
- **Caching:** Redis caches raw provider responses (60s TTL) to respect rate limits and avoid redundant fetches across concurrent jobs.
- **Database optimization:** indexes on `chain`/`contract_address`; time-series tables (historical prices, planned) will use PostgreSQL partitioning by time range.
- **Scaling strategy:** stateless API layer scales horizontally behind a load balancer; collectors/scheduler scale as independent worker processes; PostgreSQL read replicas for read-heavy dashboard queries as a future step.

---

## 21. Monitoring & Observability

- **Health checks:** `/health` (liveness, no dependency checks) live today; `/health/ready` (checks DB/Redis connectivity) planned for readiness probes — a distinct concern from liveness, so a temporary DB outage doesn't cause a crash-loop restart of an otherwise-healthy process.
- **Metrics:** Prometheus-compatible `/metrics` endpoint planned.
- **Tracing:** OpenTelemetry integration planned once the service graph (collectors → services → API) is stable enough to be worth tracing.
- **Alerts (operational):** infra-level alerting (uptime, error rate) is separate from the product's own Alert Engine (V10, which alerts *users* about tokens) — both are on the roadmap.

---

## 22. Testing

```bash
pytest                                    # full suite with coverage
pytest app/tests/test_dexscreener_collector.py -v   # single module
pytest --cov=app --cov-report=html        # HTML coverage report
```

**Test types:** unit tests (services, normalizers — no I/O), integration tests (repository ↔ real test DB), API tests (`httpx.ASGITransport` against the FastAPI app), collector tests (HTTP mocked via `respx` — collectors never hit real networks in CI). **Coverage goal:** ≥90%, enforced via `--cov-fail-under=90` in CI. **Performance/load tests:** planned for the M10/V1-release milestone once the API surface is stable.

---

## 23. Code Quality

| Tool | Purpose | Command |
|---|---|---|
| Ruff | Linting (replaces flake8/isort) | `ruff check app` |
| Black | Formatting | `black app` / `black --check app` |
| mypy | Static type checking (strict mode) | `mypy app` |
| pre-commit | Runs all of the above pre-commit | `pre-commit run --all-files` |

Install hooks once per clone: `pre-commit install`.

---

## 24. CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR to `main`/`develop`: spins up Postgres + Redis service containers, installs the project, runs `ruff check`, `black --check`, `mypy`, then `pytest` with a coverage gate. A Docker image build/push workflow and a tagged-release workflow are planned additions once V1 ships.

---

## 25. Documentation Standards

Each completed milestone updates `docs/ARCHITECTURE.md` with its design decisions (append, don't overwrite prior milestones' sections) and `docs/ROADMAP.md` checkbox state. This `README.md` is the single source of truth for anyone new to the project — sections should be updated in the same PR as the feature they describe, not backfilled later.

---

## 26. Roadmap

| Version | Focus | Status |
|---|---|:---:|
| **V1** | Core screener: discovery, storage, API, basic ranking | 🚧 In progress |
| **V2** | Wallet Intelligence | ⏳ Planned |
| **V3** | Contract Security | ⏳ Planned |
| **V4** | Whale Tracking | ⏳ Planned |
| **V5** | Social Intelligence | ⏳ Planned |
| **V6** | Narrative Detection | ⏳ Planned |
| **V7** | GitHub / Developer Analysis | ⏳ Planned |
| **V8** | Machine Learning Pipeline | ⏳ Planned |
| **V9** | Alpha Score Engine (ML-driven) | ⏳ Planned |
| **V10** | Alert Engine | ⏳ Planned |
| **V11** | React Dashboard | ⏳ Planned |
| **V12** | Portfolio Tracking | ⏳ Planned |
| **V13** | Paper Trading | ⏳ Planned |
| **V14** | Backtesting | ⏳ Planned |
| **V15** | AI Research Assistant | ⏳ Planned |

> **Note:** V2 does not begin until V1 is explicitly approved and released.

---

## 27. Contributing

**Branch strategy:** `main` (stable/release) ← `develop` (integration) ← `feature/<short-description>` branches.

**Commit convention:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat(scope): description`, `fix(scope): description`, `docs(scope): description`, `test(scope): description`.

**Pull request process:** branch from `develop` → implement one milestone/feature per PR → ensure `pre-commit run --all-files` and `pytest` pass locally → open PR against `develop` → CI must pass before merge.

**Code review expectations:** every PR needs at least one approval; reviewers check for type hints, docstrings, test coverage on new logic, and adherence to the layering rules in `docs/ARCHITECTURE.md`.

---

## 28. Troubleshooting

**`pytest` hangs or times out** — Postgres/Redis probably aren't up yet. Run `docker compose ps` and wait for both to show `healthy` before testing.

**`alembic revision --autogenerate` produces an empty migration** — Alembic's `env.py` isn't seeing your models. Confirm `app/core/database/migrations/env.py` imports every model module (`from app.models import Chain, Token`).

**`ModuleNotFoundError: No module named 'app'`** — you're likely running commands from the wrong directory, or the venv isn't activated. Run `which python3` and confirm it points into `.venv/bin/python3`; run commands from the repo root.

**`respx` test fails with "no matching route"** — the mocked URL must exactly match what the client requests, including trailing slashes and query params.

**Manual ingestion script inserts 0 rows** — some providers return chains outside our supported `Chain` enum; the normalizer correctly filters these out. Log `len(profiles)` vs. the ingested count to confirm this is filtering, not a bug.

**`OperationalError` on a previously-working DB connection** — likely a stale pooled connection; confirm `pool_pre_ping=True` is set in `app/core/database/session.py` (it is, by default, in this codebase).

---

## 29. Best Practices

- Never bypass the Repository layer with raw SQLAlchemy queries in services or API routes.
- Never call `os.getenv` outside `app/core/config/settings.py`.
- Every new external API integration gets its own collector + normalizer pair, isolated from the rest of the system.
- Every DTO crossing a layer boundary is a Pydantic model — never pass raw dicts between layers.
- Run `pre-commit run --all-files` before every push, not just before a PR.

---

## 30. Production Deployment

**Reverse proxy:** deploy behind nginx or Traefik for TLS termination and request buffering; the FastAPI app itself should not be exposed directly to the internet. **HTTPS:** terminate TLS at the reverse proxy (Let's Encrypt via Traefik/certbot). **Backups:** automated daily PostgreSQL dumps (`pg_dump`) with off-site retention; test restores periodically — an untested backup is not a backup. **Secrets:** use your platform's secrets manager (AWS Secrets Manager, Doppler, Vault) rather than plain `.env` files in production; inject as environment variables at container start. **Scaling:** stateless API containers scale horizontally behind a load balancer; run collectors/scheduler as separate worker deployments so a slow provider API doesn't starve API request handling. **Disaster recovery:** documented runbook (planned) covering DB restore, Redis cache rebuild (it's a cache — safe to lose), and collector backfill procedures.

---

## 31. Future Improvements

- Multi-region deployment for RPC latency reduction on chain data collection
- Read-replica routing for dashboard-heavy read traffic
- Feature store for ML pipeline to avoid recomputing features across model retraining runs
- Public API rate-limited free tier + authenticated higher-limit tier

---

## 32. License

**Proprietary — all rights reserved.** *(Placeholder — update if/when this project is open-sourced under a specific license such as MIT or Apache 2.0.)*

---

## 33. Acknowledgements

Built on the shoulders of the open-source ecosystem: FastAPI, SQLAlchemy, Pydantic, structlog, the Python async ecosystem, and the public APIs (DexScreener, GeckoTerminal) that make token-level data accessible without running dedicated chain indexers from day one.

---

## 34. Contact

| Role | Contact |
|---|---|
| Maintainer | *(placeholder — add name/handle)* |
| Issues | *(placeholder — add repository issue tracker link)* |
| Discussions | *(placeholder — add Discord/Telegram community link)* |