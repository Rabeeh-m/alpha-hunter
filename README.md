<div align="center">

# Alpha Hunter

**AI-Powered Crypto Intelligence Platform for Early-Stage Token Discovery**

[![Python](https://img.shields.io/badge/python-3.13%2B-blue?logo=python)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)](#)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](#)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](#)

*A transparent, explainable research tool — not a prediction engine, not financial advice.*

</div>

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Implemented Features](#2-implemented-features)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Project Structure](#5-project-structure)
6. [Modules in Detail](#6-modules-in-detail)
7. [Database Design](#7-database-design)
8. [REST API Reference](#8-rest-api-reference)
9. [Scheduler & Jobs](#9-scheduler--jobs)
10. [Alpha Scoring Engine](#10-alpha-scoring-engine)
11. [Installation](#11-installation)
12. [Local Development](#12-local-development)
13. [Environment Variables](#13-environment-variables)
14. [Testing](#14-testing)
15. [Code Quality](#15-code-quality)
16. [Next Phases & Roadmap](#16-next-phases--roadmap)
17. [License](#17-license)

---

## 1. Project Overview

### Vision
A world where anyone doing early-stage crypto research has access to the same class of on-chain and off-chain signal analysis that quantitative trading desks use internally — presented transparently, with every score traceable to the data that produced it.

### Purpose
Manual crypto research is slow, fragmented across a dozen tools, and biased toward whoever shouts loudest on social media. Alpha Hunter automates the *data collection and signal aggregation* work, leaving the human in charge of the final judgment call.

### Current State (V1 — Core Screener)
The platform is fully operational with **37 database tables** across **22 migrations**, **8 API router modules**, **6 scheduled background jobs**, a **React SPA dashboard**, and **7 intelligence services** covering token discovery, wallet analysis, contract security, social signals, narrative classification, developer activity, and whale event detection.

### Key Capabilities
- Multi-chain, multi-provider token discovery (DexScreener + GeckoTerminal)
- Liquidity, contract-risk, wallet, developer, social, and narrative analysis
- Explainable Alpha Score — every score decomposes into its contributing factors
- REST API with search, filtering, sorting, pagination
- Scheduled, automatic data refresh via APScheduler
- Real-time whale event detection
- LLM-based narrative classification (Anthropic Claude)
- React dashboard with token screener, detail views, system monitoring

### Non-Goals
- Alpha Hunter does **not** execute trades
- Alpha Hunter does **not** custody funds or private keys
- Alpha Hunter does **not** promise or predict returns
- Alpha Hunter is **not** a replacement for your own due diligence

---

## 2. Implemented Features

### Token Discovery & Ingestion (V1)
- Multi-provider token discovery from **DexScreener** (new token profiles + pairs) and **GeckoTerminal** (new pools across all supported networks)
- Protocol-based provider interface — add new data sources without changing ingestion logic
- Redis-cached HTTP clients with tenacity retry policies
- Quality gate: filters out tokens below $10 liquidity AND $10 volume (eliminates mint-and-dump junk)
- Cross-provider deduplication via upsert on `(chain, contract_address)`
- Historical snapshots recorded on every ingestion cycle

### Token Search & API (V1)
- Full-text search by token name/symbol
- Filter by chain, minimum liquidity/volume/market cap, time windows (24h/7d/30d)
- Sort by any numeric field including alpha score
- Paginated responses with total count
- OpenAPI docs at `/docs` and `/redoc`

### Alpha Score Ranking Engine (V1)
- 8 weighted factors: liquidity (0.16), volume (0.12), market cap (0.08), age (0.08), liquidity growth (0.16), contract safety (0.21), social signal (0.09), developer activity (0.10)
- Log-scale scoring for USD values (meaningful at low ranges, saturating at high ranges)
- "No data = neutral 50" convention — missing signals don't penalize scores
- Explainable breakdown stored as JSONB per token

### Wallet Intelligence (V2)
- Etherscan-based transfer log fetching for EVM chains
- Holder aggregation: raw transfers → net balances → ranked holders
- Heuristic wallet classification (top-3 holders flagged as WHALE)
- Wallet confidence scoring with upgrade logic on re-scan

### Contract Security (V3)
- GoPlus token security API integration
- Risk scoring: deducts from 100 for honeypot, rug-pull, mint functions, ownership renounce status, high buy/sell taxes
- Flags: honeypot, suspicious mint, can_take_back_ownership, hidden_owner, selfdestruct, external_call, proxy, buy_tax/sell_tax

### Whale Tracking (V4)
- Append-only whale event log (never upserted — full historical record)
- Event types: NEW_POSITION, ACCUMULATION, DISTRIBUTION
- Bounded automated scanning: top 10 tokens by alpha score (rate-limit conscious)
- Cross-token whale activity feed API

### Social Intelligence (V5)
- Telegram public channel scraping (member count, online status, message volume)
- Social scoring: member size, activity rate, growth trend
- Inorganic growth detection (sudden spikes in member count)
- Bounded scanning: top 10 tokens by alpha score (respects Telegram's non-API page scraping)

### Narrative Detection (V6)
- LLM-based narrative classification via Anthropic Claude (Haiku)
- 12 narrative categories: DeFi, Meme, Gaming, AI, Infrastructure, Privacy, DePIN, RWAs, Layer2, DAO, Launchpad, Undefined
- Per-token narrative with confidence score and reasoning
- Batch classification of never-classified tokens (20 per run, LLM cost-bounded)

### GitHub / Developer Analysis (V7)
- GitHub API integration (repo info, contributors, releases, stars, forks)
- Developer activity scoring: popularity (stars+forks), freshness (recent releases), contributor count
- "No data = neutral" — most tokens lack public repo links

### Scheduler & Automation (M5)
- 6 automated jobs with APScheduler AsyncIOScheduler
- Redis-based distributed locks (prevents concurrent execution across processes)
- Centralized job execution wrapper: locking, timing, error capture, persistence to job_runs table
- Health monitoring endpoints: `/health/scheduler`, `/health/jobs`
- CLI commands for manual job management (run, pause, resume, enable, disable)

### React Dashboard (V11)
- 7 routes: Dashboard, Screener, Token Detail, Wallets/Whales, System, Narratives, Settings
- Token screener with search, chain filter, time windows, sortable columns, pagination
- Token detail with tabbed views: Overview, Charts, Whales, Contract, Social, Developer, Narratives
- Whale activity feed
- Narrative distribution chart
- System monitoring with job cards and scheduler summary
- Dark/light theme, collapsible sidebar, animated transitions
- Responsive design with Tailwind CSS

### CLI Management
- `alpha-hunter ingest` — manual ingestion from providers
- `alpha-hunter db` — alembic upgrade/downgrade/current
- `alpha-hunter jobs` — list/run jobs
- `alpha-hunter rank` — manual ranking pass
- `alpha-hunter wallets` — wallet scanning
- `alpha-hunter whales` — whale operations
- `alpha-hunter security` — contract security scanning
- `alpha-hunter social` — social scanning
- `alpha-hunter narratives` — narrative classification

---

## 3. High-Level Architecture

```
External APIs (DexScreener, GeckoTerminal, Etherscan, GoPlus, GitHub, Telegram, Anthropic)
    |
    v
Collectors Layer (HTTP clients with Redis caching + tenacity retry)
    |
    v
Normalizers (provider-specific JSON -> internal Pydantic DTOs)
    |
    v
Service Layer (orchestration business logic — knows the sequence of operations)
    |
    v
Repository Layer (the ONLY layer that issues SQL/ORM queries)
    |
    v
Database (PostgreSQL 17 — 12+ tables, async via asyncpg)
    |
    v
API Layer (FastAPI routers — 8 modules, thin, delegate to services)
    |
    v
Frontend (React 19 SPA) / CLI (Typer) / REST clients
```

**Key patterns:**
- **Repository Pattern** — every data access goes through typed repository classes
- **Protocol-based Providers** — `TokenProvider` protocol allows plugging in new data sources
- **Dependency Injection** — FastAPI Depends() for database sessions, constructor injection for services
- **Upsert Pattern** — most tables use INSERT...ON CONFLICT
- **Event Sourcing (Whale Events)** — append-only, never upserted
- **Explainable Scoring** — every score has factor_breakdown JSONB

---

## 4. Technology Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.13+ | Core runtime |
| FastAPI | 0.115+ | Async REST framework |
| Pydantic v2 / pydantic-settings | 2.9+ | Validation, DTOs, config |
| SQLAlchemy 2.x (async) | 2.0.36+ | ORM with async support |
| Alembic | 1.14+ | Database migrations |
| APScheduler | 3.10+ | Background job scheduling |
| structlog | 24.4+ | Structured logging |
| httpx | 0.27+ | Async HTTP client |
| tenacity | 9.0+ | Retry logic |
| Typer | 0.13+ | CLI framework |
| Anthropic SDK | 0.39+ | LLM narrative classification |

### Database & Cache
| Technology | Version | Purpose |
|---|---|---|
| PostgreSQL | 17 | Primary database |
| Redis | 7+ | Caching, rate limiting, job locks |
| asyncpg | 0.30+ | Async PostgreSQL driver |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 19.2+ | UI framework |
| TypeScript | 6.0+ | Type safety |
| Vite | 8.1+ | Build tool |
| Tailwind CSS | 4.3+ | Styling |
| React Router | 7.18+ | Client-side routing |
| TanStack React Query | 5.101+ | Server state / caching |
| Zustand | 5.0+ | Client state management |
| Axios | 1.18+ | HTTP client |
| Recharts | 3.9+ | Charts |
| Framer Motion | 12.42+ | Animations |
| Lucide React | 1.24+ | Icons |
| React Hook Form | 7.81+ | Forms |
| Zod | 4.4+ | Validation |

### Testing
| Technology | Purpose |
|---|---|
| pytest / pytest-asyncio | Async-compatible test runner |
| respx | HTTP mocking for collector tests |
| pytest-cov | Coverage enforcement |
| Vitest | Frontend test runner |
| Testing Library | React component tests |

### Code Quality
| Technology | Purpose |
|---|---|
| Ruff | Linting (replaces flake8 + isort) |
| Black | Deterministic formatting |
| mypy (strict) | Static type checking |
| pre-commit | Pre-commit hook enforcement |

### DevOps
| Technology | Purpose |
|---|---|
| Docker / Docker Compose | Reproducible local + deployment environments |
| GitHub Actions | CI (planned) |

---

## 5. Project Structure

```
alpha-hunter/
├── app/
│   ├── api/                    # FastAPI routers — HTTP layer only
│   │   ├── health.py           # Health check endpoints (/health, /health/scheduler, /health/jobs)
│   │   └── v1/                 # V1 API routers (8 modules)
│   │       ├── tokens.py       # Token search, detail, snapshots
│   │       ├── jobs.py         # Job management (run, pause, resume)
│   │       ├── wallets.py      # Wallet scanning + whale events
│   │       ├── contract_security.py  # Contract security scanning
│   │       ├── social.py       # Social score scanning
│   │       ├── narratives.py   # Narrative classification
│   │       └── developer.py    # Developer activity scanning
│   ├── blockchain/             # Chain-specific utilities
│   │   └── chain_ids.py        # EIP-155 chain ID mappings
│   ├── cli/                    # Typer CLI entry points
│   │   ├── main.py             # CLI app factory
│   │   └── commands/           # Command groups (ingest, db, jobs, rank, wallets, whales, security, social, narratives)
│   ├── collectors/             # External data provider clients + normalizers
│   │   ├── base.py             # TokenProvider Protocol
│   │   ├── dexscreener_*.py    # DexScreener client, normalizer, provider
│   │   ├── geckoterminal_*.py  # GeckoTerminal client, normalizer, provider
│   │   ├── etherscan_client.py # Etherscan transfer log fetching
│   │   ├── goplus_client.py    # GoPlus contract security API
│   │   ├── github_client.py    # GitHub API (repo, contributors, releases)
│   │   ├── telegram_client.py  # Telegram channel preview scraper
│   │   └── anthropic_client.py # Claude Haiku narrative classification
│   ├── contracts/              # Contract analysis
│   │   └── risk_scoring.py     # GoPlus-based risk scoring
│   ├── core/
│   │   ├── config/             # pydantic-settings (single source of truth)
│   │   ├── database/           # SQLAlchemy engine/session + Alembic migrations (22 revisions)
│   │   ├── cache.py            # Redis cache wrapper
│   │   ├── exceptions.py       # Domain exception hierarchy
│   │   └── locks.py            # Redis-based distributed job locks
│   ├── developer/              # Developer analysis
│   │   └── scoring.py          # GitHub-based activity scoring
│   ├── ml/                     # ML pipeline placeholder (empty)
│   ├── models/                 # SQLAlchemy ORM models (12 models)
│   │   ├── token.py            # Token, Chain enum
│   │   ├── alpha_score.py      # AlphaScore with factor_breakdown
│   │   ├── token_snapshot.py   # Historical market data snapshots
│   │   ├── wallet.py           # Wallet + WalletType enum
│   │   ├── wallet_holding.py   # Token-wallet balances
│   │   ├── whale_event.py      # WhaleEvent + WhaleEventType enum
│   │   ├── contract_security.py # Contract security analysis
│   │   ├── social_score.py     # Social score + inorganic growth flag
│   │   ├── social_snapshot.py  # Telegram snapshot data
│   │   ├── narrative_classification.py # Narrative + NarrativeClassification
│   │   ├── developer_activity.py # Developer activity scores
│   │   └── job_run.py          # Job execution history
│   ├── narratives/             # Narrative analysis
│   │   └── classifier_prompt.py # LLM prompt + parser
│   ├── ranking/                # Scoring engine
│   │   └── scoring.py          # 8-factor weighted Alpha Score calculation
│   ├── repositories/           # Data access layer (Repository Pattern, 10 repos)
│   ├── scheduler/              # Background job system
│   │   ├── scheduler.py        # APScheduler setup + 6 job definitions
│   │   ├── registry.py         # Job registry + stats tracking
│   │   ├── jobs.py             # Job implementations
│   │   └── execution.py        # Central execution wrapper (locking, timing, persistence)
│   ├── schemas/                # Pydantic DTOs (API + provider payloads)
│   ├── services/               # Business logic / use-case orchestration
│   │   ├── token_ingestion_service.py
│   │   ├── ranking_service.py
│   │   ├── wallet_discovery_service.py
│   │   ├── contract_security_service.py
│   │   ├── social_intelligence_service.py
│   │   ├── narrative_classification_service.py
│   │   └── developer_intelligence_service.py
│   ├── social/                 # Social analysis
│   │   ├── scoring.py          # Telegram-based social scoring
│   │   └── telegram_parser.py  # Telegram HTML preview parser
│   ├── wallets/                # Wallet analysis
│   │   ├── classification.py   # Heuristic wallet type classification
│   │   ├── holder_aggregator.py # Transfer log → net balance aggregation
│   │   └── whale_detection.py  # New position / accumulation / distribution detection
│   ├── tests/                  # pytest suite
│   ├── main.py                 # FastAPI app factory / composition root
├── frontend/                   # React SPA
│   └── src/
│       ├── api/                # Axios API client modules (9 modules)
│       ├── components/         # Reusable UI components
│       ├── features/           # Feature-specific components
│       ├── hooks/              # React Query hooks (12 hooks)
│       ├── layouts/            # App layout, sidebar, topbar
│       ├── pages/              # Page components (7 pages)
│       ├── store/              # Zustand stores (theme, toasts)
│       ├── types/              # TypeScript type definitions
│       └── test/               # Vitest test files
├── docker/
│   └── docker-compose.yml      # PostgreSQL 17 + Redis 7
├── tests/
│   └── load/                   # Locust load testing
├── pyproject.toml              # Project metadata + tool config
├── alembic.ini                 # Migration configuration
└── README.md
```

---

## 6. Modules in Detail

### 6.1 Collectors Layer
Each external API has its own **client** (HTTP handler with caching + retry), **normalizer** (JSON → internal DTO), and **provider** (implements `TokenProvider` Protocol). This isolation means a rate-limit hit or schema change in one provider never affects others.

| Collector | Data Source | Caching | Retry |
|---|---|---|---|
| DexScreener | new token profiles + pairs | Redis 60s TTL | 3 attempts, exponential backoff |
| GeckoTerminal | new pools across networks | Redis 60s TTL | 3 attempts, exponential backoff |
| Etherscan | ERC-20 transfer logs | Redis 300s TTL | 3 attempts |
| GoPlus | token contract security | Redis 3600s TTL | 2 attempts |
| GitHub | repo info, contributors, releases | No cache | 3 attempts |
| Telegram | channel preview pages | No cache | 1 attempt |
| Anthropic | narrative classification | No cache | 2 attempts |

### 6.2 Repository Layer
All database access goes through repository classes. Key operations:

- **TokenRepository** — CRUD + search/filter/sort with whitelisted sort fields (prevents injection)
- **AlphaScoreRepository** — upsert by token_id
- **WalletRepository** — get-or-create with confidence upgrade
- **WalletHoldingRepository** — upsert with previous-balance tracking (for whale detection)
- **SocialScoreRepository / SocialSnapshotRepository** — point-in-time + score pair
- **NarrativeRepository** — upsert, list_unclassified, distribution query
- **DeveloperActivityRepository** — get/upsert

### 6.3 Service Layer
| Service | Purpose |
|---|---|
| TokenIngestionService | Multi-provider ingest with quality gate + snapshot recording |
| RankingService | 8-factor Alpha Score computation for one or all tokens |
| WalletDiscoveryService | Transfer log fetch → holder aggregation → whale event creation |
| ContractSecurityService | On-demand GoPlus scan + risk scoring |
| SocialIntelligenceService | Telegram scrape → social score + inorganic growth detection |
| NarrativeClassificationService | LLM classify + batch unclassified tokens |
| DeveloperIntelligenceService | GitHub analysis → developer activity score |

### 6.4 Scoring Modules

**Alpha Score** (`app/ranking/scoring.py`): 8 weighted factors → 0–100 composite, with per-factor breakdown stored as JSONB.

**Contract Risk** (`app/contracts/risk_scoring.py`): Starts at 100, deducts for honeypot (–40), mint function (–20), rug-pull flags (–15 each), high taxes (–5 per % above threshold). Missing data = neutral 50.

**Social Scoring** (`app/social/scoring.py`): Member size (up to 60pts), activity rate (up to 25pts), member growth rate (up to 15pts). Flags inorganic growth when member count spikes >200% in a single interval.

**Developer Scoring** (`app/developer/scoring.py`): Popularity (stars+forks, capped at 40), freshness (days since last release, capped at 30), contributor count (capped at 30). Combined linearly to 0–100.

---

## 7. Database Design

### Current Schema (12 tables)

```
tokens                    — Primary token registry. Unique on (chain, contract_address)
alpha_scores              — Computed scores with factor_breakdown JSONB per token
token_snapshots           — Point-in-time market data (price, liquidity, volume) for charts
wallets                   — Discovered wallets with type classification
wallet_holdings           — Token-wallet balance with rank
whale_events              — Append-only whale activity log (event_type, prev/new balance, change_usd)
contract_securities       — GoPlus security scan results (safety_score, flags, taxes)
social_scores             — Social media scores with factor_breakdown JSONB
token_social_snapshots    — Telegram channel point-in-time data (members, messages)
narrative_classifications — LLM-generated narrative with confidence and reasoning
developer_activities      — GitHub analysis results (score, stars, forks, contributors)
job_runs                  — Scheduled job execution history (status, duration, error)
```

### Migration Strategy
22 Alembic revisions, all generated via `alembic revision --autogenerate`. Applied via `alembic upgrade head` in CI and deployment pipelines.

---

## 8. REST API Reference

**Base URL:** `http://localhost:8000/api/v1` (local)

### Health
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/health/scheduler` | Scheduler status + aggregated job stats |
| GET | `/health/jobs` | Per-job status (enabled, last run, failure count) |

### Tokens
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tokens` | Search/filter/sort/paginate tokens |
| GET | `/api/v1/tokens/{id}` | Single token detail |
| GET | `/api/v1/tokens/{id}/snapshots` | Historical price/liquidity snapshots |

**Query parameters for `GET /api/v1/tokens`:**
- `q` — text search (name/symbol)
- `chain` — filter by chain (ethereum, base, solana, bnb, arbitrum, polygon, avalanche, optimism)
- `min_liquidity`, `min_volume`, `min_market_cap` — numeric floor filters
- `created_since`, `created_before` — ISO date range filters
- `sort` — field to sort by (prefix `-` for descending, e.g. `-alpha_score`)
- `page`, `page_size` — pagination

### Jobs
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/jobs` | List all registered jobs with stats |
| GET | `/api/v1/jobs/{id}` | Single job detail |
| POST | `/api/v1/jobs/{id}` | Trigger/run a job |

### Wallets & Whales
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tokens/{id}/wallets` | Token holder rankings |
| POST | `/api/v1/tokens/{id}/wallets` | Scan token for wallets (Etherscan) |
| GET | `/api/v1/whales/recent` | Recent whale events across all tokens |
| GET | `/api/v1/tokens/{id}/wallets/whale-events` | Whale events for specific token |

### Contract Security
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tokens/{id}/security` | Get stored security analysis |
| POST | `/api/v1/tokens/{id}/security/scan` | Trigger GoPlus security scan |

### Social
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tokens/{id}/social` | Get stored social score |
| POST | `/api/v1/tokens/{id}/social/scan` | Trigger Telegram social scan |

### Narratives
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tokens/{id}/narrative` | Get stored narrative classification |
| POST | `/api/v1/tokens/{id}/narrative/classify` | Trigger LLM narrative classification |
| GET | `/api/v1/narratives/distribution` | Aggregate narrative distribution |

### Developer Activity
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tokens/{id}/developer` | Get stored developer analysis |
| POST | `/api/v1/tokens/{id}/developer/scan` | Trigger GitHub analysis |

Interactive OpenAPI docs at `/docs` (Swagger UI) and `/redoc`.

---

## 9. Scheduler & Jobs

6 automated jobs run via APScheduler `AsyncIOScheduler`:

| Job ID | Interval | Category | Description |
|---|---|---|---|
| `refresh_dexscreener` | 90s | collector | Fetch latest token profiles + pairs |
| `refresh_geckoterminal` | 90s | collector | Fetch new pools across supported networks |
| `compute_alpha_scores` | 120s | ranking | Recompute Alpha Scores for all tokens |
| `scan_top_tokens_for_whale_activity` | 20min | whale-monitoring | Scan top-10 tokens for holder balance changes |
| `scan_top_tokens_for_social_activity` | 60min | social | Scan top-10 tokens' Telegram channels |
| `classify_unclassified_narratives` | 10min | narrative | Classify up to 20 never-classified tokens per run |

**Execution guarantees:**
- Redis-based distributed locks prevent concurrent execution
- Every execution is persisted to `job_runs` table (status, duration, error)
- `max_instances=1` — no overlapping runs
- Jobs can be paused/resumed/enabled/disabled at runtime

---

## 10. Alpha Scoring Engine

### Philosophy
Every score must be traceable to the specific data points that produced it.

### 8 Weighted Factors

| Factor | Weight | Source | Range |
|---|---|---|---|
| Liquidity | 0.16 | Log-scale from $1k (0) to $1M (100) | 0–100 |
| Volume (24h) | 0.12 | Log-scale from $1k (0) to $1M (100) | 0–100 |
| Market Cap | 0.08 | Log-scale from $10k (0) to $50M (100) | 0–100 |
| Age | 0.08 | 100 at discovery → linear decay to 0 at 30 days | 0–100 |
| Liquidity Growth | 0.16 | Neutral 50 with no history; 0–100 based on % change | 0–100 |
| Contract Safety | 0.21 | Pass-through of GoPlus safety_score; neutral 50 if unscanned | 0–100 |
| Social Signal | 0.09 | Pass-through of Telegram score; halved if inorganic growth flagged | 0–100 |
| Developer Activity | 0.10 | Pass-through of GitHub score; neutral 50 if unscanned | 0–100 |

### Explainability
The `AlphaScore.factor_breakdown` JSONB column stores every factor's raw score and weight alongside the composite, enabling the API to return the "why" alongside the "what".

---

## 11. Installation

### Prerequisites
| Requirement | Minimum Version |
|---|---|
| Python | 3.13+ |
| Docker + Docker Compose | 24+ |
| Git | any recent |

### Docker Installation (Recommended)
```bash
# Clone
git clone <repository-url> alpha-hunter
cd alpha-hunter

# Start PostgreSQL + Redis
docker compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload
```

### Manual Installation
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# Ensure PostgreSQL 17+ and Redis 7+ are running
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # Vite dev server on :5173
npm run build   # Production build
```

---

## 12. Local Development

```bash
# 1. Start infrastructure
docker compose up -d postgres redis
docker compose ps                    # confirm both are "healthy"

# 2. Set up environment
cp .env.example .env
# edit .env: set SECRET_KEY, confirm DATABASE_URL / REDIS_URL

# 3. Install + migrate
pip install -e ".[dev]"
alembic upgrade head

# 4. Start API + scheduler (scheduler starts automatically with the app)
uvicorn app.main:app --reload

# 5. Start frontend (separate terminal)
cd frontend && npm run dev

# 6. Verify
curl http://localhost:8000/health
```

### CLI Usage
```bash
# Source token ingestion
alpha-hunter ingest dexscreener
alpha-hunter ingest geckoterminal

# Database management
alpha-hunter db upgrade
alpha-hunter db current

# Job management
alpha-hunter jobs list
alpha-hunter jobs run refresh_dexscreener

# Scoring
alpha-hunter rank compute

# On-demand scans
alpha-hunter wallets scan <token-id>
alpha-hunter whales recent
alpha-hunter security scan <token-id>
alpha-hunter social scan <token-id>
alpha-hunter narratives classify <token-id>
```

---

## 13. Environment Variables

| Variable | Description | Required | Default |
|---|---|---|---|
| `SECRET_KEY` | JWT signing secret | Yes | — |
| `DATABASE_URL` | Async Postgres connection string | Yes | — |
| `REDIS_URL` | Redis connection string | Yes | — |
| `APP_NAME` | Service display name | No | `Alpha Hunter` |
| `ENVIRONMENT` | `local` / `development` / `staging` / `production` | No | `local` |
| `DEBUG` | Enable FastAPI debug mode | No | `false` |
| `LOG_LEVEL` | Minimum log level | No | `INFO` |
| `LOG_JSON` | JSON logs (prod) vs console (dev) | No | `true` |
| `JWT_ALGORITHM` | JWT signing algorithm | No | `HS256` |
| `DATABASE_POOL_SIZE` | SQLAlchemy pool size | No | `10` |
| `ETHEREUM_RPC_URL` | Ethereum RPC endpoint | No | — |
| `ETHERSCAN_API_KEY` | Etherscan API key | No | — |
| `GITHUB_TOKEN` | GitHub API token | No | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | No | — |
| `CELERY_BROKER_URL` | Celery broker (defaults to REDIS_URL) | No | — |

See `.env.example` for the complete up-to-date list.

---

## 14. Testing

```bash
# Backend tests
pytest                                          # full suite with coverage
pytest -v                                       # verbose
pytest --cov=app --cov-report=html              # HTML coverage report

# Frontend tests
cd frontend && npm test                          # Vitest
npm run test:coverage                            # With coverage

# Load tests
locust -f tests/load/locustfile.py --headless    # Locust load testing
```

**Current coverage:** 6 backend tests (settings, job locks) + 3 frontend tests (UI components). Service-layer and integration tests are a priority for the next phase.

---

## 15. Code Quality

| Tool | Purpose | Command |
|---|---|---|
| Ruff | Linting | `ruff check app` |
| Black | Formatting | `black app` / `black --check app` |
| mypy (strict) | Type checking | `mypy app` |
| pre-commit | All of the above | `pre-commit run --all-files` |

Install hooks: `pre-commit install`

**Best practices enforced:**
- Never bypass the Repository layer with raw SQLAlchemy in services or API routes
- Never call `os.getenv` outside `app/core/config/settings.py`
- Every external API integration gets its own collector + normalizer pair
- Every layer-crossing DTO is a Pydantic model
- Logging via structlog with context vars, never `print()` or logging.basicConfig

---

## 16. Next Phases & Roadmap

### Phase 1 — Production Hardening & Testing (Immediate)

**Goal:** Move from functional prototype to production-ready system with comprehensive test coverage, CI/CD, and operational tooling.

**Tasks:**

1. **Comprehensive Test Suite**
   - Unit tests for all 7 services (mock repositories, assert correct orchestration)
   - Integration tests for all 10 repositories against a real test database
   - API integration tests (httpx.ASGITransport against FastAPI app)
   - Collector tests with respx HTTP mocking
   - Frontend component tests for all pages and features
   - Target: ≥85% code coverage

2. **CI/CD Pipeline**
   - GitHub Actions workflow: lint → type-check → test → coverage gate on every PR
   - Docker image build + push workflow for tagged releases
   - Pre-commit hooks configuration (`.pre-commit-config.yaml`)
   - Automated Alembic migration checking in CI

3. **Error Handling & Resilience**
   - Graceful degradation when individual providers are unavailable
   - Circuit breaker pattern for external API calls
   - Dead-letter queue for failed job executions
   - Enhanced error reporting with structured error codes

4. **Production Docker Setup**
   - Production Dockerfile (multi-stage: slim, non-root user, HEALTHCHECK)
   - Production docker-compose with api + scheduler as separate services
   - nginx/Traefik reverse proxy configuration
   - Automated PostgreSQL backups (pg_dump with off-site retention)

### Phase 2 — Wallet Intelligence V2 (Advanced)

**Goal:** Move beyond basic holder aggregation to smart-money tracking, wallet clustering, and sophisticated pattern detection.

**Tasks:**

1. **Smart Money Tagging**
   - VC wallet address database (seed from公开 sources)
   - Exchange hot wallet detection (known address patterns)
   - KOL/influencer wallet discovery
   - Automated tag propagation via transaction graph analysis
   - Confidence scoring for heuristic-based tags

2. **Wallet Clustering**
   - Same-owner wallet detection (funding source analysis)
   - Cluster-level balance aggregation
   - Multi-wallet accumulation pattern detection
   - Cluster health scoring (diversity, vintage, success rate)

3. **Accumulation/Selling Pattern Detection**
   - Time-weighted average price (TWAP) vs. spot detection
   - Tiered accumulation identification (slow/fast/aggressive)
   - Distribution vs. profit-taking classification
   - Pattern confidence scoring with historical accuracy tracking

4. **Cross-Token Wallet Intelligence**
   - Track wallet activity across multiple tokens
   - Identify early buyers across launches
   - Wallet-level alpha score (historical pick accuracy)
   - Repeat-founder token detection

### Phase 3 — ML Pipeline V8

**Goal:** Build a production ML pipeline for feature engineering, model training, and inference — replacing hand-tuned scoring weights with data-driven models.

**Tasks:**

1. **Feature Engineering Pipeline**
   - Historical feature store (time-series features for each token)
   - Technical indicators (price action, volatility, liquidity depth)
   - Wallet-derived features (holder concentration, whale ratio, smart money ratio)
   - Social features (sentiment trajectory, engagement velocity, inorganic growth confidence)
   - Developer features (commit frequency, team size estimate, code quality proxies)
   - Narrative features (narrative momentum, category competition)
   - Contract features (complexity score, ownership patterns, upgrade proxies)
   - Cross-token features (ecosystem correlations, sector rotations)

2. **Label Engineering**
   - Outcome definition: "success" vs. "failure" at 7/14/30 day horizons
   - Success criteria (multiple definitions for robustness):
     - Price appreciation ≥X% with sustained liquidity
     - Holder count growth
     - Volume sustainability
     - Combined composite label
   - Label validation through manual review of edge cases
   - Survival analysis for censored tokens (still trading at evaluation)

3. **Model Training Pipeline**
   - Baseline models: logistic regression, random forest, XGBoost, LightGBM, CatBoost
   - Time-series-aware cross-validation (no lookahead bias)
   - Hyperparameter optimization (Optuna/Ray Tune)
   - Model ensemble strategies (stacking, voting, weighted averaging)
   - Calibration curve analysis (reliability diagrams)
   - Feature importance analysis (SHAP, permutation importance)

4. **Model Evaluation & Selection**
   - Backtesting framework (simulate historical decisions)
   - Profitability simulation (if you'd acted on top-X scores)
   - Sharpe ratio / information coefficient analysis
   - Overfitting detection (train/test decay curves)
   - Model explainability (SHAP values per prediction)

5. **Inference Pipeline**
   - Real-time feature computation service
   - Model serving (ONNX runtime for latency-critical path)
   - Prediction caching with TTL based on feature staleness
   - Model versioning and A/B testing framework
   - Drift detection (feature drift, prediction drift, concept drift)
   - Automated model retriggering on drift alerts

6. **MLOps Infrastructure**
   - Feature store (Redis for online, PostgreSQL for offline)
   - Model registry (MLflow tracking server)
   - Experiment tracking with full reproducibility
   - Pipeline orchestration (Prefect/Dagster/Airflow)
   - Monitoring dashboard (feature distributions, prediction distributions, model performance)

### Phase 4 — Alpha Score Engine V9 (ML-Driven)

**Goal:** Replace the hand-tuned V1 Alpha Score with an ML-driven engine that learns optimal weights and discovers non-linear relationships from historical data.

**Tasks:**

1. **ML-Enhanced Scoring**
   - ML model output as primary score component (60% weight)
   - Hand-tuned factors retain 40% weight (fallback + explainability bridge)
   - Dynamic weight adjustment based on model confidence
   - Ensemble of horizon-specific models (7-day, 14-day, 30-day)

2. **Model Interpretability Layer**
   - SHAP waterfall charts per token score
   - Natural language explanations ("This token scores highly primarily due to...")
   - Counterfactual analysis ("What would need to change for this score to increase by 20 points?")
   - Confidence interval for every score prediction

3. **Continuous Learning**
   - Online learning pipeline (model updates with new data without full retrain)
   - Automated retraining schedule (weekly full retrain)
   - Champion/challenger model evaluation
   - Feedback loop from user-reported outcomes

### Phase 5 — Alert Engine V10

**Goal:** Push-based notification system for token events and score changes.

**Tasks:**

1. **Alert Configuration**
   - User-configurable alert rules (web UI + API)
   - Alert triggers:
     - Score threshold crossings (enters/exits top X%)
     - Whale events (new position, accumulation, distribution)
     - Contract changes (ownership transfer, mint enable)
     - Social inorganicity flags
     - Price/volume/liquidity breakout detection
     - New narrative emergence
   - Cooldown periods to prevent alert fatigue
   - Rate-limited alert delivery

2. **Delivery Channels**
   - Telegram bot integration (rich messages with token cards)
   - Discord webhook integration (embeds with live data)
   - Slack webhook integration
   - Email digest (daily/weekly summary)
   - Webhook API for custom integrations
   - In-app notification feed in React dashboard

3. **Alert Management**
   - Alert history and audit log
   - Acknowledge/mute/snooze controls
   - Escalation policies (if no response in X minutes)
   - Alert analytics (most triggered rules, false positive rate)

### Phase 6 — React Dashboard V11 (Full Build)

**Goal:** Complete the React SPA with all planned pages, real-time updates, and polished UX.

**Tasks:**

1. **Dashboard Overhaul**
   - Metrics cards: total tokens tracked, new today, avg alpha score, top narrative
   - Top movers (24h score change leaders)
   - Recent whale activity timeline
   - Narrative momentum chart
   - Alert feed (unread count, recent alerts)
   - System health summary
   - Token discovery rate chart

2. **Enhanced Token Detail**
   - Complete all 9 tabs (Overview, Charts, Whales, Liquidity, Transactions, Social, Developer, Narratives, Risk)
   - Liquidity tab: depth chart, pool composition, historical liquidity curve
   - Transactions tab: recent large transactions, top buyers/sellers
   - Risk tab: aggregated risk flags, honeypot analysis, tax analysis
   - Price chart: multiple timeframes, volume overlay, MA indicators
   - Score breakdown radar chart
   - Similar tokens recommendation

3. **Portfolio Tracking (V12 foundation)**
   - Watchlist creation and management (persisted to backend)
   - Portfolio balance tracking (manual entry initially)
   - Token-level P&L with cost basis tracking
   - Alpha Score-based rebalancing suggestions
   - Portfolio-level aggregated metrics

4. **UX Polish**
   - Real-time updates via WebSocket (score changes, new tokens, whale events)
   - Infinite scroll in token lists
   - Keyboard shortcuts
   - Saved filters and views
   - Export to CSV/JSON
   - Mobile-responsive layouts for all pages
   - Skeleton loading states everywhere
   - Dark mode refinements (custom themes, AMOLED mode)

### Phase 7 — Portfolio Tracking V12 & Paper Trading V13

**Goal:** Full portfolio tracking with paper trading simulation.

**Tasks:**

1. **Portfolio Management**
   - Multi-portfolio support (separate strategies/accounts)
   - Transaction logging (buy/sell/transfer with fees)
   - Realized/unrealized P&L tracking
   - Performance metrics (ROI, Sharpe, max drawdown, win rate)
   - Tax lot accounting (FIFO, LIFO, specific identification)
   - Portfolio rebalancing tracking

2. **Paper Trading Engine**
   - Simulated trade execution with configurable slippage
   - Virtual balance management (per-portfolio)
   - Order types: market, limit, stop-loss, take-profit
   - Fill simulation based on actual pool data
   - Execution delay modeling (realistic latency)
   - Paper trading performance vs. actual token performance
   - Leaderboard (optional, for community features)

3. **Strategy Backtesting V14 Foundation**
   - Strategy definition DSL (entry/exit rules, position sizing)
   - Historical fill simulation with realistic liquidity constraints
   - Performance reporting with benchmark comparisons
   - Parameter optimization framework

### Phase 8 — Backtesting V14 & AI Research Assistant V15

**Goal:** Full historical backtesting engine and conversational AI interface.

**Tasks:**

1. **Backtesting Engine**
   - Historical data replay at configurable tick frequency
   - Strategy definition: entry conditions, exit conditions, position sizing, risk management
   - Portfolio simulation with fees, slippage, liquidity constraints
   - Batch backtest runner for parameter sweeps
   - Performance analytics suite:
     - Return metrics (CAGR, cumulative return, monthly return)
     - Risk metrics (volatility, VaR, CVaR, max drawdown, ulcer index)
     - Risk-adjusted metrics (Sharpe, Sortino, Calmar, Information Ratio)
     - Trade statistics (win rate, avg win/loss, profit factor, expectancy)
     - Market correlation analysis (beta, alpha, R-squared)
   - Monte Carlo simulation for robustness testing
   - Walk-forward analysis for strategy validation
   - Benchmark comparison (buy-and-hold, top-10 equal weight, etc.)

2. **AI Research Assistant**
   - Natural language query interface ("Which tokens have strong developer activity but low social scores?")
   - Conversational token analysis ("Why did this token's score drop 15 points?")
   - Automated research report generation
   - Pattern recognition queries ("Has this whale's accumulation pattern been predictive in the past?")
   - Chat history with session management
   - Multi-turn analysis with context retention
   - Integration with LLM (Claude Sonnet/Opus for complex reasoning)
   - RAG pipeline for on-chain + off-chain data retrieval
   - Citation generation (every claim traceable to source data)

### Phase 9 — Infrastructure & Production Scale

**Goal:** Enterprise-grade infrastructure for production-scale operation.

**Tasks:**

1. **Multi-Region Deployment**
   - Global load balancing (AWS Route53 / Cloudflare)
   - Regional RPC endpoint selection for latency reduction
   - Cross-region database replication
   - Disaster recovery runbook

2. **Read Replica Architecture**
   - PostgreSQL read replicas for dashboard-heavy read traffic
   - Automatic read/write splitting in repository layer
   - Replica lag monitoring and read-your-writes consistency

3. **Public API Tier**
   - Free tier: rate-limited, historical data only, 1-hour delayed
   - Pro tier: real-time, full endpoints, webhook delivery
   - Enterprise tier: dedicated infrastructure, SLA, custom integrations
   - API key management + usage tracking
   - Developer portal with documentation + playground

4. **Monitoring & Observability**
   - Prometheus metrics endpoint (/metrics)
   - Grafana dashboards (system, business, ML)
   - OpenTelemetry distributed tracing
   - AlertManager for operational alerts
   - SLO/SLI tracking and reporting
   - Cost attribution per provider/service

---

## 17. License

**Proprietary — all rights reserved.** *(Placeholder — update if/when this project is open-sourced under a specific license such as MIT or Apache 2.0.)*
