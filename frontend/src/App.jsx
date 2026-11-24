/* PART 3 - Front end.
 *
 * Build one page that shows tenant sales data from your own API:
 *   - a table of lease units
 *   - at least one working filter (mall or category)
 *   - one chart of sales over time
 *
 * Styling is not assessed. Component structure, state handling, and
 * loading/error states are.
 *
 * recharts is already installed if you want it.
 */
import { useEffect, useState } from "react";

export default function App() {
  const [health, setHealth] = useState("checking...");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setHealth(d.status))
      .catch(() => setHealth("cannot reach API"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui", padding: 24 }}>
      <h1>DBI Take-Home</h1>
      <p>API status: {health}</p>
      <p>Replace this page with your answer to Part 3.</p>
    </main>
  );
}
