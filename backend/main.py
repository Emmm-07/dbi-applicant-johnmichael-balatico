"""PART 2 - API.

Run with:  uvicorn main:app --reload --port 8000
Docs at:   http://localhost:8000/docs

CORS is already configured for the Vite dev server - don't spend time on it.

Build these endpoints over the data your pipeline loaded:

  GET /api/tenants
      Paginated list of lease units. Supports filtering by mall and by
      category, and a page size the caller controls.

  GET /api/tenants/{tenant_code}
      One lease unit with its monthly sales history.

  GET /api/sales/summary
      Total gross sales grouped by mall or by category (caller chooses),
      for a date range the caller provides.

Design the response shapes yourself. Validation and error behaviour are
part of what is being assessed.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import get_conn

app = FastAPI(title="DBI Take-Home API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Already works. Use it to confirm your setup before you start."""
    return {"status": "ok"}
