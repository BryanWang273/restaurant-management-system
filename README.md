# Restaurant Management System

A single-restaurant management system: menu, inventory, and order management on a
FastAPI + PostgreSQL backend, a Next.js frontend, and an AI agent that turns raw
consumption data into reorder recommendations.

The interesting part isn't the CRUD — it's the **AI inventory agent**: an
OpenAI-SDK tool-calling loop where Python owns every number (consumption rates,
days-until-stockout, reorder quantities) and the LLM only ever reasons over
pre-computed summaries. See [The AI Recommendation Agent](#the-ai-recommendation-agent)
below for why that split matters.

## Live Demo

- **App**: https://restaurant-management-system-kappa-five.vercel.app
- **API docs**: https://restaurant-management-api-1iux.onrender.com/docs

Both run on free tiers — the backend cold-starts (~30–50s) after periods of
inactivity, so the first request after a while will feel slow. That's expected,
not broken.

## Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [The AI Recommendation Agent](#the-ai-recommendation-agent)
- [Groq Compatibility Notes](#groq-compatibility-notes)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)

## Architecture

```
web/ (Next.js)  ──HTTP──▶  app/ (FastAPI)  ──SQL──▶  PostgreSQL
   Server Components            │
   & Server Actions             ▼
                          routers/   → HTTP layer: request/response, status codes
                          services/  → business logic, DB queries
                          models/    → SQLAlchemy ORM tables
                          schemas/   → Pydantic request/response contracts
```

The backend follows a strict layering: **routers** depend on **services**, services
depend on **models**, and **schemas** define the shape of everything crossing the
HTTP boundary. Nothing skips a layer — a router never touches the ORM directly, and
a service never builds an HTTP response.

The frontend fetches directly from the FastAPI backend **server-side only** (Next.js
Server Components and Server Actions) — the browser never calls the API directly, so
the backend needs no CORS configuration at all.

The AI agent (`app/services/ai_recommendation_service.py`) sits inside the same
service layer as everything else, but calls out to an LLM mid-request via
OpenAI-SDK-style tool calling. See [below](#the-ai-recommendation-agent) for how it's
scoped.

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — HTTP layer
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) — ORM
- [Alembic](https://alembic.sqlalchemy.org/) — migrations
- [Pydantic](https://docs.pydantic.dev/) / `pydantic-settings` — schemas & config
- [PostgreSQL 16](https://www.postgresql.org/) — database (via Docker)
- [openai-python](https://github.com/openai/openai-python) v3 — LLM tool-calling client, pointed at [Groq](https://groq.com/) rather than OpenAI (see [below](#groq-compatibility-notes))
- `pytest` — testing

**Frontend**
- [Next.js 16](https://nextjs.org/) (App Router, Server Components, Server Actions, Turbopack)
- [React 19](https://react.dev/)
- [Tailwind CSS 4](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/) (Radix primitives)
- TypeScript, hand-mirrored types against the backend's Pydantic schemas (no codegen step)

**Infra**
- Docker Compose for local PostgreSQL

## Project Structure

```
app/
  core/            # settings (env vars) and DB engine/session setup
  models/          # SQLAlchemy tables: inventory_items, menu_items, recipe_items,
                    #   orders, order_items, usage_events
  schemas/         # Pydantic request/response models
  services/        # business logic — one module per domain area
  routers/         # FastAPI route handlers, one router per resource
  main.py          # app assembly (include_router calls)
alembic/           # migrations
tests/             # pytest suite (currently covers the AI recommendation service)
seed_data.py       # resets the DB to a realistic demo menu (see Getting Started)
web/
  src/app/         # Next.js routes (dashboard, menu, orders, inventory, recommendations)
  src/components/  # shared UI components
  src/lib/         # API client, hand-mirrored types, formatting helpers
```

## Getting Started

### Prerequisites

- Python 3.13
- Node.js 22+ and npm
- Docker Desktop (for PostgreSQL)
- A [Groq](https://console.groq.com/) API key (free tier works) for the AI agent — everything else runs without it

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

This starts Postgres 16 on `localhost:5432` (see `docker-compose.yml` for
credentials — `postgres` / `devpass`, database `restaurant`).

### 2. Backend setup

```bash
python -m venv venv
venv/Scripts/activate      # Windows
source venv/bin/activate   # macOS/Linux

pip install -r requirements-dev.txt   # includes pytest on top of requirements.txt
```

Create a `.env` file in the repo root:

```bash
DATABASE_URL=postgresql://postgres:devpass@localhost:5432/restaurant

# AI recommendation agent — this project uses Groq's free, OpenAI-compatible
# API rather than paying for OpenAI directly. The key still goes under
# OPENAI_API_KEY because that's what the openai-python SDK reads.
OPENAI_API_KEY=your-groq-api-key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=openai/gpt-oss-120b
```

> If `OPENAI_API_KEY` is unset, the rest of the app works fine — only the
> `/ai/inventory-recommendations` endpoint is affected, and it fails with a clear
> 503 rather than crashing anything.

Run migrations:

```bash
alembic upgrade head
```

Seed realistic demo data (a 10-item menu with recipes and matching inventory,
including a few ingredients seeded just under their reorder point):

```bash
python seed_data.py
```

This is safe to re-run — it always clears prior menu/inventory/order data before
reseeding, so it doubles as a "reset the demo" command.

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs are then available at `http://localhost:8000/docs`.

### 3. Frontend setup

```bash
cd web
npm install
```

Create `web/.env.local` (see `web/.env.example`):

```bash
API_URL=http://127.0.0.1:8000
```

Start the dev server:

```bash
npm run dev
```

The app is now running at `http://localhost:3000`.

## The AI Recommendation Agent

`POST /ai/inventory-recommendations` generates reorder suggestions for every
low-stock ingredient. The core design decision: **Python does the math, the LLM does
the judgment.**

An LLM asked to compute consumption rates and reorder quantities directly from raw
event logs will get the arithmetic wrong often enough to matter — and a wrong
reorder quantity is the kind of error that costs real money. So the split is:

- **Python** aggregates `usage_events` into daily consumption rates and
  days-until-stockout *before* the model ever sees them (`_low_stock_snapshot`,
  `_menu_items_for_ingredient` in `ai_recommendation_service.py`).
- **The LLM** only ever reasons over those pre-computed summaries — deciding
  urgency, writing the human-readable justification, and tying the recommendation
  back to which menu items are actually driving the demand. It never does the
  arithmetic itself.

The agent runs a bounded tool-calling loop (max 6 iterations) with two tools:

| Tool | Returns |
|---|---|
| `list_low_stock_items` | Every item at/below its reorder point, with daily consumption rate and estimated days until stockout |
| `get_menu_items_for_ingredient` | Which menu items use a given ingredient, and how many servings were ordered recently |

Once the model has what it needs, it returns a structured response — validated
against a Pydantic schema (`InventoryRecommendationResponse`) — with a reorder
quantity, urgency (`low`/`medium`/`high`), and reasoning per item.

## Groq Compatibility Notes

This project uses Groq's OpenAI-compatible endpoint instead of paying for OpenAI.
"OpenAI-compatible" doesn't mean *identical* — three real incompatibilities were
found empirically while building this, none obviously documented anywhere:

1. **Model names aren't portable.** `llama-3.3-70b-versatile` returned a 404 on this
   account — always check `GET /v1/models` against the actual account rather than
   trusting a remembered model name; catalogs and access vary. `openai/gpt-oss-120b`
   is what's currently used, since it explicitly advertises both `tools` and
   `structured_outputs` support.
2. **Empty-argument tool schemas break Groq's validator.** `openai.pydantic_function_tool`
   generates `{"required": [], "properties": {}}` in strict mode for a field-less
   tool — valid JSON Schema, but Groq rejects it as `"'required' present but
   'properties' is missing"`. Fixed by hand-writing that one tool's schema without a
   `required` key.
3. **`tools` and `response_format` can't be combined in a single request on Groq**
   (OpenAI supports this). Groq errors with `"json mode cannot be combined with
   tool/function calling"`. Fixed by splitting the agent loop into two phases: a
   tools-only gathering loop (`.create()`), then a separate, tools-free `.parse()`
   call for the final structured output.

If this ever moves back to real OpenAI, or to a different "compatible" provider,
re-verify these three rather than assuming the code ports cleanly — they're Groq
workarounds, not general best practice.

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/menu-items/` | List menu items (with recipes) |
| POST | `/menu-items/` | Create a menu item |
| PATCH / DELETE | `/menu-items/{id}` | Update / delete a menu item |
| POST / DELETE | `/menu-items/{id}/recipe-items[/{id}]` | Attach / remove a recipe ingredient |
| GET | `/inventory-items/` | List inventory items |
| GET | `/inventory-items/low-stock` | List items at/below their reorder point |
| POST | `/inventory-items/` | Create an inventory item |
| PATCH / DELETE | `/inventory-items/{id}` | Update / delete an inventory item |
| GET | `/orders/` | List orders |
| POST | `/orders/` | Place an order (validates stock, deducts inventory) |
| POST | `/ai/inventory-recommendations` | Generate AI reorder recommendations |

Full interactive docs: `http://localhost:8000/docs` once the backend is running.

## Running Tests

```bash
pytest tests/ -v
```

Tests run against the same database as `DATABASE_URL` — each test runs inside a
transaction that's rolled back afterward, so nothing written by a test is ever
persisted, even against a database with real data in it. The suite covers the AI
recommendation service: the pure consumption-rate math, the DB-backed aggregation
queries, and the tool-calling loop (against a fake OpenAI client, so no network
calls or API costs).
