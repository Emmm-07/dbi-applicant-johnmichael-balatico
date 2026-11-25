import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

const MALLS = ["SM Mall of Asia", "SM Megamall", "SM North EDSA", "SM Southmall"];
const CATEGORIES = ["Food & Beverage", "Apparel", "Services", "Electronics", "Home"];
const PAGE_SIZE = 15;

function useTenants(mall, category, page) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    setState(s => ({ ...s, loading: true, error: null }));
    const params = new URLSearchParams({ page, page_size: PAGE_SIZE });
    if (mall) params.set("mall", mall);
    if (category) params.set("category", category);

    fetch(`/api/tenants?${params}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(data => setState({ data, loading: false, error: null }))
      .catch(err => setState({ data: null, loading: false, error: String(err) }));
  }, [mall, category, page]);

  return state;
}

function useTenantDetail(tenantCode) {
  const [state, setState] = useState({ detail: null, loading: false, error: null });

  useEffect(() => {
    if (!tenantCode) { setState({ detail: null, loading: false, error: null }); return; }
    setState(s => ({ ...s, loading: true, error: null }));

    fetch(`/api/tenants/${encodeURIComponent(tenantCode)}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(detail => setState({ detail, loading: false, error: null }))
      .catch(err => setState({ detail: null, loading: false, error: String(err) }));
  }, [tenantCode]);

  return state;
}

export default function App() {
  const [mall, setMall] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [selectedCode, setSelectedCode] = useState(null);

  const { data, loading, error } = useTenants(mall, category, page);
  const { detail, loading: detailLoading, error: detailError } = useTenantDetail(selectedCode);

  const totalPages = data?.pagination?.total_pages ?? 1;

  function handleMallChange(v) { setMall(v); setPage(1); setSelectedCode(null); }
  function handleCategoryChange(v) { setCategory(v); setPage(1); setSelectedCode(null); }
  function handleRowClick(code) { setSelectedCode(prev => prev === code ? null : code); }

  return (
    <main style={styles.main}>
      <h1 style={{ margin: "0 0 20px" }}>Tenant Sales</h1>

      {/* Filters */}
      <div style={styles.filterBar}>
        <label style={styles.label}>
          Mall
          <select value={mall} onChange={e => handleMallChange(e.target.value)} style={styles.select}>
            <option value="">All malls</option>
            {MALLS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </label>

        <label style={styles.label}>
          Category
          <select value={category} onChange={e => handleCategoryChange(e.target.value)} style={styles.select}>
            <option value="">All categories</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>

        {data && (
          <span style={styles.count}>{data.pagination.total} units found</span>
        )}
      </div>

      {/* Table */}
      {error && <p style={styles.error}>Failed to load tenants: {error}</p>}

      <div style={{ overflowX: "auto" }}>
        <table style={styles.table}>
          <thead>
            <tr style={{ background: "#f5f5f5" }}>
              {["Code", "Name", "Mall", "Category", "Floor Area (sqm)"].map(h => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={styles.placeholder}>Loading…</td></tr>
            ) : data?.data?.length === 0 ? (
              <tr><td colSpan={5} style={styles.placeholder}>No results</td></tr>
            ) : (
              data?.data?.map(row => {
                const isSelected = row.tenant_code === selectedCode;
                return (
                  <tr
                    key={`${row.tenant_code}-${row.mall}`}
                    onClick={() => handleRowClick(row.tenant_code)}
                    style={{
                      cursor: "pointer",
                      background: isSelected ? "#e8f0fe" : "white",
                      outline: isSelected ? "2px solid #3b82f6" : "none",
                      outlineOffset: -1,
                    }}
                    onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = "#fafafa"; }}
                    onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = "white"; }}
                  >
                    <td style={styles.td}>{row.tenant_code}</td>
                    <td style={styles.td}>{row.tenant_name}</td>
                    <td style={styles.td}>{row.mall}</td>
                    <td style={styles.td}>{row.category}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>
                      {row.floor_area_sqm != null ? Number(row.floor_area_sqm).toLocaleString() : "—"}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {!loading && data && (
        <div style={styles.pagination}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            style={styles.btn}
          >
            ← Prev
          </button>
          <span style={{ fontSize: 13, color: "#555" }}>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            style={styles.btn}
          >
            Next →
          </button>
        </div>
      )}

      {/* Sales history chart */}
      {selectedCode && (
        <div style={styles.chartSection}>
          {detailLoading && <p style={{ color: "#666" }}>Loading sales history…</p>}
          {detailError && <p style={styles.error}>Failed to load detail: {detailError}</p>}
          {detail && (
            <>
              <h2 style={{ margin: "0 0 4px" }}>
                {detail.tenant_name}
                <span style={styles.detailMeta}>
                  {detail.mall} · {detail.category}
                </span>
              </h2>
              <p style={styles.chartLabel}>Monthly gross sales — click another row to compare</p>

              {detail.sales_history.length === 0 ? (
                <p style={{ color: "#666" }}>No sales history available.</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart
                    data={detail.sales_history}
                    margin={{ top: 8, right: 32, bottom: 8, left: 16 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="report_month" tick={{ fontSize: 11 }} />
                    <YAxis
                      tickFormatter={v => `₱${(v / 1_000_000).toFixed(1)}M`}
                      tick={{ fontSize: 11 }}
                      width={72}
                    />
                    <Tooltip
                      formatter={v =>
                        [`₱${Number(v).toLocaleString("en-PH", { minimumFractionDigits: 2 })}`, "Gross Sales"]
                      }
                    />
                    <Line
                      type="monotone"
                      dataKey="gross_sales"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </>
          )}
        </div>
      )}
    </main>
  );
}

const styles = {
  main: {
    fontFamily: "system-ui, sans-serif",
    padding: "24px",
    maxWidth: 1100,
    margin: "0 auto",
    color: "#1a1a1a",
  },
  filterBar: {
    display: "flex",
    gap: 16,
    marginBottom: 16,
    alignItems: "flex-end",
    flexWrap: "wrap",
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    fontSize: 13,
    fontWeight: 600,
    color: "#444",
  },
  select: {
    padding: "7px 10px",
    borderRadius: 6,
    border: "1px solid #ccc",
    fontSize: 14,
    minWidth: 170,
    background: "white",
  },
  count: { fontSize: 13, color: "#777", alignSelf: "center" },
  error: { color: "#c0392b", margin: "8px 0" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 14 },
  th: {
    padding: "9px 12px",
    textAlign: "left",
    fontWeight: 600,
    borderBottom: "2px solid #ddd",
    whiteSpace: "nowrap",
  },
  td: { padding: "8px 12px", borderBottom: "1px solid #eee" },
  placeholder: { padding: 20, textAlign: "center", color: "#888" },
  pagination: {
    display: "flex",
    gap: 10,
    marginTop: 14,
    alignItems: "center",
  },
  btn: {
    padding: "5px 14px",
    borderRadius: 6,
    border: "1px solid #ccc",
    cursor: "pointer",
    background: "white",
    fontSize: 13,
  },
  chartSection: {
    marginTop: 36,
    borderTop: "2px solid #eee",
    paddingTop: 24,
  },
  detailMeta: {
    fontWeight: 400,
    fontSize: 14,
    color: "#666",
    marginLeft: 10,
  },
  chartLabel: { fontSize: 13, color: "#666", margin: "2px 0 16px" },
};
