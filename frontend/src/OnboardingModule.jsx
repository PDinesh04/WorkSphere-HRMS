import React, { useEffect, useState } from "react";
import api from "./api";

export default function OnboardingModule({ isHR = false }) {
  const [tasks, setTasks] = useState([]);
  const [employeeId, setEmployeeId] = useState("");
  const [taskName, setTaskName] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadTasks() {
    try {
      const params = employeeId ? { employee_id: Number(employeeId) } : {};
      const response = await api.get("/onboarding/", { params });
      setTasks(response.data);
      setError("");
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load onboarding tasks.");
    }
  }
  useEffect(() => { loadTasks(); }, []);

  async function createTask(e) {
    e.preventDefault();
    try {
      await api.post("/onboarding/", {
        employee_id: Number(employeeId), task_name: taskName, due_date: dueDate || null
      });
      setTaskName(""); setDueDate(""); setMessage("Onboarding task created.");
      await loadTasks();
    } catch (e) {
      setError(e.response?.data?.detail || "Could not create task.");
    }
  }

  async function toggleStatus(task) {
    try {
      const status = task.status === "COMPLETED" ? "PENDING" : "COMPLETED";
      await api.patch(`/onboarding/${task.id}`, { status });
      await loadTasks();
    } catch (e) {
      setError(e.response?.data?.detail || "Could not update task.");
    }
  }

  const completed = tasks.filter(t => t.status === "COMPLETED").length;
  const progress = tasks.length ? Math.round(completed / tasks.length * 100) : 0;
  return <section className="panel">
    <h2>Employee Onboarding</h2>
    <p>{completed} of {tasks.length} tasks completed ({progress}%).</p>
    <progress value={progress} max="100" style={{ width: "100%" }} />
    {error && <p role="alert">{error}</p>}{message && <p>{message}</p>}
    {isHR && <form className="formgrid" onSubmit={createTask}>
      <label>Employee ID</label>
      <input type="number" min="1" required value={employeeId} onChange={e => setEmployeeId(e.target.value)} />
      <label>Task name</label>
      <input required minLength="2" maxLength="200" value={taskName} onChange={e => setTaskName(e.target.value)} />
      <label>Due date</label>
      <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
      <button className="primary" type="submit">Assign task</button>
    </form>}
    <div className="tablewrap"><table><thead><tr><th>Task</th><th>Due date</th><th>Status</th><th>Action</th></tr></thead>
      <tbody>{tasks.map(task => <tr key={task.id}><td>{task.task_name}</td><td>{task.due_date || "—"}</td><td>{task.status}</td>
        <td><button type="button" onClick={() => toggleStatus(task)}>Mark {task.status === "COMPLETED" ? "pending" : "completed"}</button></td></tr>)}
        {!tasks.length && <tr><td colSpan="4">No onboarding tasks found.</td></tr>}</tbody></table></div>
  </section>;
}
