
import { useEffect, useState } from "react";
import api from "./api";

export default function AnalyticsDashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/analytics/summary")
      .then((response) => {
        setStats(response.data);
        setError("");
      })
      .catch((err) => {
        console.error(
          "Analytics error:",
          err.response?.status,
          err.response?.data || err.message
        );
        setError(
          err.response?.data?.detail ||
            "Unable to load analytics. Please check your login and permissions."
        );
      });
  }, []);

  if (error) return <p>{error}</p>;
  if (!stats) return <p>Loading analytics...</p>;

  const cards = [
    ["Total Employees", stats.total_employees],
    ["Active Employees", stats.active_employees],
    ["Total Resignations", stats.total_resignations],
    ["Pending Resignations", stats.pending_resignations],
    ["Total Settlements", stats.total_settlements],
    ["Pending Settlements", stats.pending_settlements],
  ];

  return (
    <div style={{ padding: "24px" }}>
      <h1>HR Analytics Dashboard</h1>
      <p>Overview of your workforce and exit processes.</p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
          marginTop: "24px",
        }}
      >
        {cards.map(([label, value]) => (
          <div
            key={label}
            style={{
              padding: "20px",
              border: "1px solid #ddd",
              borderRadius: "12px",
              background: "#fff",
            }}
          >
            <p>{label}</p>
            <h2>{value ?? 0}</h2>
          </div>
        ))}
      </div>
    </div>
  );
}
