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
from fastapi import FastAPI, HTTPException, Query
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


@app.get("/api/tenants")
def list_tenants(
    mall: str | None = Query(None, description="Filter by mall name (case-insensitive)"),
    category: str | None = Query(None, description="Filter by category (case-insensitive)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
):
    conditions, params = [], []

    if mall:
        conditions.append("LOWER(mall) = LOWER(?)")
        params.append(mall)
    if category:
        conditions.append("LOWER(category) = LOWER(?)")
        params.append(category)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = get_conn()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM (SELECT 1 FROM sales {where} GROUP BY tenant_code, mall)",
            params,
        ).fetchone()[0]

        offset = (page - 1) * page_size
        rows = conn.execute(
            f"""
            SELECT tenant_code,
                   tenant_name,
                   mall,
                   category,
                   MAX(floor_area_sqm) AS floor_area_sqm
              FROM sales
             {where}
             GROUP BY tenant_code, mall
             ORDER BY LOWER(tenant_name), tenant_code
             LIMIT ? OFFSET ?
            """,
            params + [page_size, offset],
        ).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    return {
        "data": [dict(r) for r in rows],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        },
    }


@app.get("/api/tenants/{tenant_code}")
def get_tenant(tenant_code: str):
    conn = get_conn()
    try:
        unit = conn.execute(
            """
            SELECT tenant_code,
                   tenant_name,
                   mall,
                   category,
                   MAX(floor_area_sqm) AS floor_area_sqm
              FROM sales
             WHERE LOWER(tenant_code) = LOWER(?)
             GROUP BY tenant_code, mall
            """,
            (tenant_code,),
        ).fetchone()

        if unit is None:
            raise HTTPException(status_code=404, detail=f"Tenant '{tenant_code}' not found")

        history = conn.execute(
            """
            SELECT report_month,
                   SUM(gross_sales) AS gross_sales
              FROM sales
             WHERE LOWER(tenant_code) = LOWER(?)
             GROUP BY report_month
             ORDER BY report_month
            """,
            (tenant_code,),
        ).fetchall()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    return {
        **dict(unit),
        "sales_history": [dict(r) for r in history],
    }


@app.get("/api/sales/summary")
def sales_summary(
    group_by: str = Query(..., pattern="^(mall|category)$", description="Group results by 'mall' or 'category'"),
    date_from: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="Start month inclusive, format YYYY-MM"),
    date_to: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="End month inclusive, format YYYY-MM"),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")

    conditions, params = [], []

    if date_from:
        conditions.append("report_month >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("report_month <= ?")
        params.append(date_to)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = get_conn()
    try:
        rows = conn.execute(
            f"""
            SELECT {group_by} AS group_key,
                   SUM(gross_sales)  AS total_gross_sales,
                   COUNT(DISTINCT tenant_code || '|' || mall) AS unit_count
              FROM sales
             {where}
             GROUP BY {group_by}
             ORDER BY total_gross_sales DESC
            """,
            params,
        ).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    return {
        "group_by": group_by,
        "date_from": date_from,
        "date_to": date_to,
        "data": [dict(r) for r in rows],
    }
