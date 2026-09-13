# Closed-Loop Autonomous Data Incident Agent

A modular FastAPI backend that demonstrates `DETECT -> INVESTIGATE -> FIX -> CONTROL -> SIMULATE -> VERIFY -> RISK -> DEPLOY -> LEARN` over the supplied incident-platform dataset.

## Data placement

- **Exasol**: customers, products, orders, order items, payments, shipments, daily metrics, and quality metrics.
- **PostgreSQL**: incidents, fixes, approvals, deployments, risk, audit, lineage, schema history, and pipeline logs.
- **Qdrant**: incident memory. The local demo uses `.local-state/memory.json` when Qdrant is unavailable.

The supplied platform at `/Users/admin/Downloads/autonomous_data_incident_platform` is the seed source. The clean CSVs are never permanently corrupted.

## Run locally

```bash
cp .env.example .env
python -m pip install -r requirements.txt
python -m app.demo
uvicorn app.main:app --reload
```

API: http://localhost:8000/docs

Start operational services with `docker compose up -d postgres qdrant`. Set the real Exasol credentials in `.env`, then run `make seed`. On macOS, grant Local Network access to the terminal/VS Code process if Exasol Personal cannot expose `127.0.0.1:8563`.

## Tests

```bash
pytest -q
```

## Demo

`python -m app.demo` runs SCN-02 end to end with deterministic investigation, SQL policy validation, SQLite sandbox simulation, verification, approval, deployment snapshot, rollback availability, and memory storage. The API supports all ten scenario definitions from `failure_scenarios.csv`; SCN-02 and SCN-03 are the fully exercised demos. The mock provider is safe by default: LLM reasoning may be added behind the agent interface, while deterministic controls always decide execution.

## Mock keys

`.env.example` ends with replaceable mock values for PostgreSQL, Qdrant, and OpenAI. Replace them before enabling those integrations; no credentials are returned by the API.
