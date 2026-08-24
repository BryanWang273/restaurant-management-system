FROM python:3.13-slim

WORKDIR /app

# All backend dependencies are pure-Python or ship prebuilt wheels
# (psycopg2-binary included), so there's nothing a multi-stage build
# would strip out — a single stage keeps this simple.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY seed_data.py .

# Render (and most PaaS hosts) inject the port to bind via $PORT rather
# than using a fixed port, so it can't be hardcoded here.
EXPOSE 8000

# Migrations run here, before uvicorn starts, rather than as a separate
# pre-deploy step — Render's pre-deploy command requires a paid instance
# type, so this is the free-tier-compatible equivalent (and it keeps
# local `docker compose up` and the deployed container on the same path).
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
