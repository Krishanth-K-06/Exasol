from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
import pyexasol

from app.config.settings import settings
from app.config.database import get_db, check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.PROJECT_NAME} [{settings.ENVIRONMENT}]")
    is_connected = check_db_connection()
    if is_connected:
        print("Connected to Exasol successfully.")
    else:
        print("Warning: Could not connect to Exasol at startup.")
    yield
    print(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "database": "Exasol",
        "dsn": settings.EXASOL_DSN,
    }


@app.get("/health")
def health_check(db: pyexasol.ExaConnection = Depends(get_db)):
    """
    Health check endpoint verifying API status and Exasol database connectivity.
    """
    try:
        val = db.execute("SELECT 1 AS PING").fetchval()
        db_status = "healthy" if val == 1 else "unexpected response"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database": {
            "type": "Exasol",
            "dsn": settings.EXASOL_DSN,
            "status": db_status,
        },
    }


@app.get("/api/v1/schemas")
def list_schemas(db: pyexasol.ExaConnection = Depends(get_db)):
    """
    Returns available schemas from Exasol catalog.
    """
    try:
        statement = db.execute("SELECT SCHEMA_NAME, SCHEMA_OWNER FROM EXA_ALL_SCHEMAS ORDER BY SCHEMA_NAME")
        rows = statement.fetchall()
        return {
            "count": len(rows),
            "schemas": [{"name": row[0], "owner": row[1]} for row in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
