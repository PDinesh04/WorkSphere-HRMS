
import { useEffect, useState } from "react";
import api from "./api";

export default function SystemSettings() {
  const [settings, setSettings] = useState({
    company_name: "WorkSphere",
    email: "",
    phone: "",
    address: "",
    working_hours_start: "09:00:00",
    working_hours_end: "18:00:00",
    weekly_holidays: "Saturday,Sunday",
  });
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.get("/settings/company")
      .then((res) => setSettings({
        ...res.data,
        working_hours_start: res.data.working_hours_start || "09:00:00",
        working_hours_end: res.data.working_hours_end || "18:00:00",
      }))
      .catch((err) => {
        console.error("Settings error:", err.response?.data || err);
        setMessage("Unable to load settings. Please log in.");
      });
  }, []);

  const handleChange = (e) => {
    setSettings({ ...settings, [e.target.name]: e.target.value });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setMessage("");

    try {
      const res = await api.put("/settings/company", settings);
      setSettings({
        ...res.data,
        working_hours_start: res.data.working_hours_start || "09:00:00",
        working_hours_end: res.data.working_hours_end || "18:00:00",
      });
      setMessage("Company settings saved successfully!");
    } catch (err) {
      setMessage(
        err.response?.data?.detail ||
          "Unable to save settings. ADMIN access is required."
      );
    }
  };

  const fields = [
    ["company_name", "Company Name"],
    ["email", "Company Email"],
    ["phone", "Phone"],
    ["address", "Address"],
    ["working_hours_start", "Working Hours Start"],
    ["working_hours_end", "Working Hours End"],
    ["weekly_holidays", "Weekly Holidays"],
  ];

  return (
    <div style={{ padding: 24, maxWidth: 650 }}>
      <h2>System Settings</h2>
      <p>Configure company details and working hours.</p>

      <form onSubmit={handleSave}>
        {fields.map(([name, label]) => (
          <div key={name} style={{ marginBottom: 16 }}>
            <label htmlFor={name}>{label}</label>
            <input
              id={name}
              name={name}
              type={
                name === "email" ? "email" :
                name.startsWith("working_hours") ? "time" : "text"
              }
              value={
                name.startsWith("working_hours")
                  ? (settings[name] || "").slice(0, 5)
                  : settings[name] || ""
              }
              onChange={handleChange}
              required={name === "company_name"}
              style={{
                display: "block",
                width: "100%",
                padding: 10,
                marginTop: 5,
                boxSizing: "border-box",
              }}
            />
          </div>
        ))}

        <button type="submit">Save Settings</button>
      </form>

      {message && <p>{message}</p>}
    </div>
  );
}
