# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands use `uv`. Never use `pip` or `python` directly.

```bash
# Run the API server
uv run uvicorn app.main:app --reload

# Database migrations
uv run alembic upgrade head         # apply migrations
uv run alembic revision --autogenerate -m "description"  # generate migration
uv run alembic current              # check current revision
uv run alembic downgrade -1         # roll back one

# Run the data ingest (loads Scryfall bulk JSON into the DB)
uv run python -m app.ingest.loader

# Add dependencies
uv add <package>
```

## Architecture

AetherGyre is a FastAPI card-database backend for Magic: The Gathering cube management, backed by PostgreSQL.

### Configuration

`app/core/config.py` — `Settings` (pydantic-settings) is the single source of truth. It loads `DATABASE_URL` from `.env`. Both `app/db/session.py` and `alembic/env.py` import `settings` from here. Never hardcode connection strings elsewhere.

### Data model — two-layer card design

Cards have a deliberate two-table split:

- **`OracleCard`** (`oracle_cards`) — one row per unique card identity (name, rules text, mana cost, etc.). Keyed on `oracle_id` (UUID from Scryfall).
- **`Card`** (`cards`) — one row per physical printing (set, collector number, art, rarity). FK → `oracle_cards.oracle_id` and `sets.id`.
- **`CardImage`** (`card_images`) — per-size image URLs for each printing. Cascade-deleted with `Card`.

This means "search by name" queries join `Card` → `OracleCard`, while "all versions" queries start at `OracleCard` and load `cards` relationship.

### API surface

- `app/main.py` — mounts the FastAPI app, creates tables on startup (`Base.metadata.create_all`), has the `/cards/{name}` GET route directly.
- `app/api/router.py` — `APIRouter` with `/cards/search` and `/cards/{oracle_id}/all-versions`. **Note:** this router is not yet mounted in `main.py`.
- `app/api/deps.py` — `get_db()` dependency that yields a `SessionLocal`.

### Schemas — two coexisting files

- `app/schemas/card.py` — older `OracleCardSchema` / `CardSchema` used by the route in `main.py`.
- `app/schemas/schemas.py` — newer `CardSearchResponse` / `CardHistoryResponse` used by `router.py`, uses pydantic v2 `model_config` and field aliases for nested relationships.

### Ingest

`app/ingest/loader.py` — streams the Scryfall `default-cards.json` bulk file via `ijson` (avoids loading the full file into RAM). Upserts in batches using PostgreSQL `INSERT ... ON CONFLICT DO NOTHING`. The `JSON_FILE` path at the top of the file must be updated to the local download location. **Note:** `loader.py` still has a hardcoded `DATABASE_URL`; it should be updated to use `app.core.config.settings`.

### Known model conflicts

`app/db/models/cube.py` and `app/db/models/association.py` both define a `CubeCard` class mapped to `cube_cards`. The version in `cube.py` is the canonical one (used by migrations); `association.py` is a scratch file and should not be imported.
