
import { useEffect, useState } from "react";
import axios from "axios";

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        const token = localStorage.getItem("token");

        const response = await axios.get(
          "http://127.0.0.1:8000/employees/",
          {
            headers: token
              ? { Authorization: `Bearer ${token}` }
              : {},
          }
        );

        setEmployees(
          Array.isArray(response.data)
            ? response.data
            : response.data.items || []
        );
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load employees. Please log in and try again."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchEmployees();
  }, []);

  if (loading) return <p>Loading employees...</p>;
  if (error) return <p>{error}</p>;

  return (
    <div style={{ padding: "24px" }}>
      <h1>Employee Management</h1>
      <p>Total employees: {employees.length}</p>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          marginTop: "20px",
        }}
      >
        <thead>
          <tr>
            {["ID", "Name", "Designation", "Department", "Salary", "Status"]
              .map((heading) => (
                <th
                  key={heading}
                  style={{ padding: "12px", border: "1px solid #ddd" }}
                >
                  {heading}
                </th>
              ))}
          </tr>
        </thead>

        <tbody>
          {employees.map((employee) => (
            <tr key={employee.id}>
              <td style={{ padding: "10px", border: "1px solid #ddd" }}>
                {employee.id}
              </td>
              <td style={{ padding: "10px", border: "1px solid #ddd" }}>
                {employee.full_name}
              </td>
              <td style={{ padding: "10px", border: "1px solid #ddd" }}>
                {employee.designation}
              </td>
              <td style={{ padding: "10px", border: "1px solid #ddd" }}>
                {employee.department}
              </td>
              <td style={{ padding: "10px", border: "1px solid #ddd" }}>
                {employee.salary}
              </td>
              <td style={{ padding: "10px", border: "1px solid #ddd" }}>
                {employee.status}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
