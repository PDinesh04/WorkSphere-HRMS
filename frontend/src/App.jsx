
import React, { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import api from "./api";
import OnboardingModule from "./OnboardingModule";
import AnalyticsDashboard from "./AnalyticsDashboard";
import Employees from "./pages/Employees";
import SystemSettings from "./SystemSettings";
function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const change = e => setForm({ ...form, [e.target.name]: e.target.value });
  async function submit(e) {
    e.preventDefault(); setError("");
    try {
      if (mode === "register") {
        await api.post("/auth/register", form);
        setMode("login");
        setError("Account created. Please log in.");
      } else {
        const res = await api.post("/auth/login", { username: form.username, password: form.password });
        localStorage.setItem("worksphere_token", res.data.access_token);
        onLogin(res.data.user);
      }
    } catch (err) { setError(err.response?.data?.detail || "Request failed. Is the backend running?"); }
  }
  return <div className="auth"><div className="brand">W<span>S</span></div><h1>WorkSphere</h1><p className="muted">Human Resources, made simpler.</p>
    <div className="tabs"><button className={mode==="login"?"active":""} onClick={()=>{setMode("login");setError("")}}>Login</button><button className={mode==="register"?"active":""} onClick={()=>{setMode("register");setError("")}}>Register</button></div>
    <form onSubmit={submit}>
      {mode==="register" && <><label>Full name</label><input name="full_name" value={form.full_name} onChange={change} required/><label>Email</label><input name="email" type="email" value={form.email} onChange={change} required/></>}
      <label>Username</label><input name="username" value={form.username} onChange={change} required/>
      <label>Password (minimum 8 characters)</label><input name="password" type="password" value={form.password} onChange={change} minLength="8" required/>
      <button className="primary" type="submit">{mode==="login"?"Sign in":"Create account"}</button>
    </form>{error && <p className="notice">{error}</p>}<p className="muted small">New registrations receive the EMPLOYEE role. An administrator must assign HR/Admin roles.</p>
  </div>;
}

function Dashboard({ user, onLogout }) {
  const [section, setSection] = useState("Overview");
  const [data, setData] = useState([]);
  const [message, setMessage] = useState("");
  const [profile, setProfile] = useState(null);
  const [leaveForm, setLeaveForm] = useState({ leave_type:"CASUAL", start_date:"", end_date:"", reason:"" });
  const [resignationForm, setResignationForm] = useState({
  reason: "",
  notice_period: 30,
});
  const [payrollForm, setPayrollForm] = useState({ employee_id:"", month:new Date().toISOString().slice(0,7), basic_salary:"", allowances:"0", deductions:"0", bonus:"0" });
  const [policyForm, setPolicyForm] = useState({ leave_type:"CASUAL", total_days_allowed:12 });
  const [employeeForm, setEmployeeForm] = useState({ user_id:"", full_name:"", designation:"", department:"", salary:"0", status:"ACTIVE" });
  const [userList, setUserList] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [shiftForm, setShiftForm] = useState({name:"Morning", start_time:"09:00", end_time:"17:00"});
  const [assignForm, setAssignForm] = useState({employee_id:"", shift_id:""});
  const [performanceForm, setPerformanceForm] = useState({employee_id:"", review_period:"2026-Q4", rating:5, feedback:""});
  const [documentEmployee, setDocumentEmployee] = useState("");
  const [documentFile, setDocumentFile] = useState(null);
  const [searchForm, setSearchForm] = useState({q:"", department:"", role:"", status:"", attendance_status:"", min_rating:""});
  const hr = ["HR","ADMIN"].includes(user.role), admin = user.role==="ADMIN";
  async function load() {
    try {
      if (section==="Overview") {
        if (hr) setDashboard((await api.get("/dashboard")).data);
        else setProfile((await api.get("/employees/me")).data);
      } else {
        const urls = { Employees:"/employees", Attendance:"/attendance", Leaves:"/leaves", Resignations:"/resignations/", Payroll:"/payroll", Notifications:"/notifications", "Leave balances":"/leave-balances", "Leave policies":"/leave-policies", "User management":"/admin/users", Shifts:"/shifts", "Shift assignments":"/employee-shifts", "Leave calendar":"/leave-calendar", Documents:"/documents", Performance:"/performance", Reports:"/analytics/summary", "My Shift":"/employee-shifts/me" };
        if (urls[section]) {
          const result = await api.get(urls[section]); setData(result.data);
          if(section==="User management") setUserList(result.data);
        }
      }
    } catch(e) { setMessage(e.response?.data?.detail || "Could not load data. Check your permissions and backend."); }
  }
  useEffect(()=>{ load(); },[section]);
  useEffect(()=>{ if(section!=="Notifications") return; const timer=setInterval(()=>{api.get("/notifications").then(r=>setData(r.data)).catch(()=>{});},30000); return ()=>clearInterval(timer); },[section]);
  async function act(fn, success) { setMessage(""); try { await fn(); setMessage(success); await load(); } catch(e) { setMessage(e.response?.data?.detail || "Action failed"); } }
  function list(items) {
    if (!items?.length) return <p className="muted">No records found.</p>;
    return <div className="tablewrap"><table><thead><tr>{Object.keys(items[0]).map(k=><th key={k}>{k.replaceAll("_"," ")}</th>)}{section==="Leaves"&&hr&&<th>Actions</th>}{section==="User management"&&admin&&<th>Role</th>}{section==="Documents"&&<th>Download</th>}{section==="Notifications"&&<th>Action</th>}</tr></thead><tbody>{items.map((item,i)=><tr key={item.id??i}>{Object.entries(item).map(([k,v])=><td key={k}>{typeof v==="object"&&v!==null?JSON.stringify(v):String(v??"—")}</td>)}{section==="Leaves"&&hr&&<td>{item.status==="PENDING"&&<><button onClick={()=>act(()=>api.patch(`/leaves/${item.id}/decision`,{status:"APPROVED"}),"Leave approved")}>Approve</button> <button className="danger" onClick={()=>act(()=>api.patch(`/leaves/${item.id}/decision`,{status:"REJECTED"}),"Leave rejected")}>Reject</button></>}</td>}{section==="User management"&&admin&&<td><select value={item.role} onChange={e=>act(()=>api.patch(`/admin/users/${item.id}`,{role:e.target.value,is_active:item.is_active}),"User updated")}><option>EMPLOYEE</option><option>HR</option><option>ADMIN</option></select></td>}{section==="Documents"&&<td><button onClick={async()=>{try{const r=await api.get(`/documents/${item.id}/download`,{responseType:"blob"});const url=URL.createObjectURL(r.data);const a=document.createElement("a");a.href=url;a.download=item.file_name||"document";a.click();URL.revokeObjectURL(url);}catch(e){setMessage(e.response?.data?.detail||"Download failed");}}}>Download</button></td>}{section==="Notifications"&&!item.is_read&&<td><button onClick={()=>act(()=>api.patch(`/notifications/${item.id}/read`),"Notification marked read")}>Mark read</button></td>}{section==="Notifications"&&item.is_read&&<td>Read</td>}</tr>)}</tbody></table></div>;
  }
  const sections = ["Overview","My profile","Attendance","Leaves","Resignations","Leave balances","Payroll","Notifications","Documents","Performance","My Shift","Onboarding","Analytics",...(hr?["Employees","Leave policies","Shifts","Shift assignments","Leave calendar","Reports","Advanced search"]:[]),...(admin?["User management","Run attendance automation", "System Settings"]:[] )];
  return <div className="layout"><aside><div className="brand smallbrand">W<span>S</span></div><h2>WorkSphere</h2><p className="muted">{user.username} · {user.role}</p>{sections.map(s=><button key={s} className={section===s?"nav active":"nav"} onClick={()=>{setSection(s);setMessage("");}}>{s}</button>)}<button className="nav logout" onClick={onLogout}>Sign out</button></aside>
  <main><header><div><p className="eyebrow">HUMAN RESOURCES</p><h1>{section}</h1></div><span className="role">{user.role}</span></header>
  {message&&<div className="notice">{message}</div>}
  {section==="Overview" && (hr ? dashboard ? <div className="cards">{Object.entries(dashboard).map(([k,v])=><div className="metric" key={k}><p>{k.replaceAll("_"," ")}</p><strong>{v !== null && typeof v === "object"? JSON.stringify(v): String(v ?? "—")}</strong></div>)}</div> : <p>Loading overview…</p> : <div className="panel"><h3>Welcome back, {user.username}</h3><p>Your self-service workspace is ready.</p>{profile&&<p>{profile.employee.full_name} · {profile.employee.department||"Department not set"}</p>}</div>)}
  {section==="My profile" && <div className="panel">{profile ? <pre>{JSON.stringify(profile,null,2)}</pre> : <button onClick={()=>act(async()=>setProfile((await api.get("/employees/me")).data),"Profile loaded")}>Load profile</button>}</div>}
  {section==="Onboarding"&&<OnboardingModule isHR={hr} />}
  {section === "System Settings" && admin && <SystemSettings />}
  {section==="Analytics" && hr && <AnalyticsDashboard />}
  {["Employees","Attendance","Leaves","Leave balances","Payroll","Notifications","Leave policies","User management","Shifts","Shift assignments","Leave calendar","Documents","Performance","Advanced search"].includes(section)&&list(data)}
  {section==="Resignations"&&<div className="panel"><h3>{hr ? "Resignation requests" : "Submit resignation"}</h3><form className="formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/resignations/",{reason:resignationForm.reason,notice_period:Number(resignationForm.notice_period)}),"Resignation submitted");setResignationForm({reason:"",notice_period:30});}}><label>Reason</label><textarea minLength={3} maxLength={1000} required value={resignationForm.reason} onChange={e=>setResignationForm({...resignationForm,reason:e.target.value})}/><label>Notice period (days)</label><input type="number" min="0" max="365" required value={resignationForm.notice_period} onChange={e=>setResignationForm({...resignationForm,notice_period:e.target.value})}/><button className="primary">Submit resignation</button></form><h3>Resignation history</h3>{!data?.length?<p className="muted">No resignation requests found.</p>:<div className="tablewrap"><table><thead><tr><th>ID</th><th>Employee ID</th><th>Reason</th><th>Notice period</th><th>Status</th><th>Created at</th>{hr&&<th>Actions</th>}</tr></thead><tbody>{data.map(item=><tr key={item.id}><td>{item.id}</td><td>{item.employee_id}</td><td>{item.reason}</td><td>{item.notice_period}</td><td>{item.status}</td><td>{item.created_at}</td>{hr&&<td>{item.status==="PENDING"?<><button onClick={()=>act(()=>api.patch(`/resignations/${item.id}/decision`,{status:"APPROVED"}),"Resignation approved")}>Approve</button> <button className="danger" onClick={()=>act(()=>api.patch(`/resignations/${item.id}/decision`,{status:"REJECTED"}),"Resignation rejected")}>Reject</button></>:"Processed"}</td>}</tr>)}</tbody></table></div>}</div>}
  {section==="Reports"&&data&&<div className="cards">{Object.entries(data).filter(([k,v])=>!Array.isArray(v)).map(([k,v])=><div className="metric" key={k}><p>{k.replaceAll("_"," ")}</p><strong>
  {v !== null && typeof v === "object"
    ? JSON.stringify(v)
    : String(v ?? "—")}
</strong></div>)}{Array.isArray(data.departments)&&<div className="panel"><h3>Department summary</h3>{list(data.departments)}</div>}</div>}
  {section==="My Shift"&&<div className="panel"><h3>My assigned shift</h3>{data?.assigned===false?<p>No shift assigned yet. Contact HR.</p>:data?.shift_name?<p>{data.shift_name}: {data.start_time} – {data.end_time}</p>:<button onClick={()=>act(async()=>setData((await api.get("/employee-shifts/me")).data),"Shift loaded")}>Load shift</button>}</div>}
  {section==="Shifts"&&admin&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/shifts",shiftForm),"Shift created");}}><h3>Create shift</h3><label>Name</label><select value={shiftForm.name} onChange={e=>setShiftForm({...shiftForm,name:e.target.value})}><option>Morning</option><option>Evening</option><option>Night</option></select><label>Start time</label><input type="time" required value={shiftForm.start_time} onChange={e=>setShiftForm({...shiftForm,start_time:e.target.value})}/><label>End time</label><input type="time" required value={shiftForm.end_time} onChange={e=>setShiftForm({...shiftForm,end_time:e.target.value})}/><button className="primary">Create shift</button></form>}
  {section==="Shift assignments"&&hr&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/employee-shifts",{employee_id:Number(assignForm.employee_id),shift_id:Number(assignForm.shift_id)}),"Shift assigned");}}><h3>Assign shift</h3><label>Employee ID</label><input type="number" min="1" required value={assignForm.employee_id} onChange={e=>setAssignForm({...assignForm,employee_id:e.target.value})}/><label>Shift ID</label><input type="number" min="1" required value={assignForm.shift_id} onChange={e=>setAssignForm({...assignForm,shift_id:e.target.value})}/><button className="primary">Assign / update shift</button><p className="muted small">Use IDs shown in Employees and Shifts lists.</p></form>}
  {section==="Leave calendar"&&hr&&<div className="panel"><h3>Approved team leave</h3><p className="muted">Calendar data is listed by employee and date range. Use GET /leave-calendar?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD for a custom range.</p></div>}
  {section==="Documents"&&<form className="panel formgrid" onSubmit={async e=>{e.preventDefault(); if(!documentFile){setMessage("Choose a file first");return;} const fd=new FormData();fd.append("file",documentFile);setMessage("");try{await api.post(hr?`/documents?employee_id=${Number(documentEmployee)}`:"/documents",fd,{headers:{"Content-Type":"multipart/form-data"}});setMessage("Document uploaded");setDocumentFile(null);await load();}catch(err){setMessage(err.response?.data?.detail||"Document upload failed");}}}><h3>Upload employee document</h3>{hr&&<><label>Employee ID</label><input type="number" min="1" required value={documentEmployee} onChange={e=>setDocumentEmployee(e.target.value)}/></>}<label>Document (PDF, image, DOC/DOCX; max 10 MB)</label><input type="file" required accept=".pdf,.png,.jpg,.jpeg,.doc,.docx" onChange={e=>setDocumentFile(e.target.files?.[0]||null)}/><button className="primary">Upload document</button></form>}
  {section==="Performance"&&hr&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/performance",{...performanceForm,employee_id:Number(performanceForm.employee_id),rating:Number(performanceForm.rating)}),"Performance review saved");}}><h3>Add performance review</h3><label>Employee ID</label><input type="number" min="1" required value={performanceForm.employee_id} onChange={e=>setPerformanceForm({...performanceForm,employee_id:e.target.value})}/><label>Review period</label><input required value={performanceForm.review_period} onChange={e=>setPerformanceForm({...performanceForm,review_period:e.target.value})}/><label>Rating (1–5)</label><select value={performanceForm.rating} onChange={e=>setPerformanceForm({...performanceForm,rating:e.target.value})}><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select><label>Feedback</label><textarea required value={performanceForm.feedback} onChange={e=>setPerformanceForm({...performanceForm,feedback:e.target.value})}/><button className="primary">Save review</button></form>}
  {section==="Advanced search"&&hr&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(async()=>{const params=Object.fromEntries(Object.entries(searchForm).filter(([k,v])=>v!==""));const result=await api.get("/employees/search",{params});setData(result.data);},"Search complete");}}><h3>Search and filter employees</h3>{Object.keys(searchForm).map(k=><React.Fragment key={k}><label>{k.replaceAll("_"," ")}</label>{["role","status","attendance_status"].includes(k)?<select value={searchForm[k]} onChange={e=>setSearchForm({...searchForm,[k]:e.target.value})}><option value="">Any</option>{(k==="role"?["EMPLOYEE","HR","ADMIN"]:k==="status"?["ACTIVE","INACTIVE"]:["PRESENT","LATE","ABSENT","HALF_DAY"]).map(v=><option key={v}>{v}</option>)}</select>:<input value={searchForm[k]} type={k==="min_rating"?"number":"text"} min={k==="min_rating"?1:undefined} max={k==="min_rating"?5:undefined} onChange={e=>setSearchForm({...searchForm,[k]:e.target.value})}/>}</React.Fragment>)}<button className="primary">Search employees</button></form>}
  {section==="Run attendance automation"&&admin&&<div className="panel"><h3>Run absence marking</h3><p>Marks assigned employees absent when their shift has ended and no attendance record exists for today. The same process also runs automatically at 23:59 on the backend host.</p><button className="primary" onClick={()=>act(()=>api.post("/automation/attendance/run"),"Attendance automation completed")}>Run now</button></div>}
  {section==="Attendance"&&<div className="actions"><button className="primary" onClick={()=>act(()=>api.post("/attendance/check-in"),"Checked in")}>Check in</button><button onClick={()=>act(()=>api.post("/attendance/check-out"),"Checked out")}>Check out</button></div>}
  {section==="Leaves"&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/leaves",leaveForm),"Leave request submitted");}}><h3>Apply for leave</h3><label>Type</label><select value={leaveForm.leave_type} onChange={e=>setLeaveForm({...leaveForm,leave_type:e.target.value})}><option>SICK</option><option>CASUAL</option><option>PAID</option></select><label>Start date</label><input type="date" required value={leaveForm.start_date} onChange={e=>setLeaveForm({...leaveForm,start_date:e.target.value})}/><label>End date</label><input type="date" required value={leaveForm.end_date} onChange={e=>setLeaveForm({...leaveForm,end_date:e.target.value})}/><label>Reason</label><textarea required value={leaveForm.reason} onChange={e=>setLeaveForm({...leaveForm,reason:e.target.value})}/><button className="primary">Submit leave request</button></form>}
  {section==="Employees"&&hr&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/employees",{...employeeForm,user_id:Number(employeeForm.user_id),salary:Number(employeeForm.salary)}),"Employee created");}}><h3>Add employee profile</h3>{Object.keys(employeeForm).map(k=><React.Fragment key={k}><label>{k.replaceAll("_"," ")}</label><input required={["user_id","full_name"].includes(k)} value={employeeForm[k]} onChange={e=>setEmployeeForm({...employeeForm,[k]:e.target.value})}/></React.Fragment>)}<button className="primary">Add employee</button><p className="muted small">Register the user's account first; use its user ID.</p></form>}
     {section === "Employees" && hr && (
    <div className="panel">
      <h3>Employee CSV Import / Export</h3>

      {/* Import CSV */}
      <form
        onSubmit={async (e) => {
          e.preventDefault();

          const input = e.currentTarget.elements.namedItem("csvFile");
          const file = input?.files?.[0];

          if (!file) {
            setMessage("Please select a CSV file.");
            return;
          }

          const formData = new FormData();
          formData.append("file", file);

          try {
            const response = await api.post(
              "/employees/import/csv",
              formData
            );

            setMessage(
              `Import completed: ${response.data.imported} imported, ${response.data.skipped} skipped.`
            );

            e.currentTarget.reset();
            await load();
          } catch (error) {
            setMessage(
              error.response?.data?.detail || "CSV import failed."
            );
          }
        }}
      >
        <label htmlFor="csvFile">Choose employee CSV file</label>

        <input
          id="csvFile"
          name="csvFile"
          type="file"
          accept=".csv,text/csv"
          required
        />

        <button className="primary" type="submit">
          Upload CSV
        </button>
      </form>

      <hr />

      {/* Export CSV */}
      <button
        type="button"
        className="primary"
        onClick={async () => {
          try {
            const response = await api.get("/employees/export/csv", {
              responseType: "blob",
            });

            const url = window.URL.createObjectURL(response.data);
            const link = document.createElement("a");

            link.href = url;
            link.download = "worksphere_employees.csv";

            document.body.appendChild(link);
            link.click();
            link.remove();

            window.URL.revokeObjectURL(url);
            setMessage("Employee CSV exported successfully.");
          } catch (error) {
            setMessage(
              error.response?.data?.detail || "Employee export failed."
            );
          }
        }}
      >
        Export Employees CSV
      </button>
    </div>
  )}

  {section==="Payroll"&&hr&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/payroll",{...payrollForm,employee_id:Number(payrollForm.employee_id),basic_salary:Number(payrollForm.basic_salary),allowances:Number(payrollForm.allowances),deductions:Number(payrollForm.deductions),bonus:Number(payrollForm.bonus)}),"Payroll generated");}}><h3>Generate payroll</h3>{Object.keys(payrollForm).map(k=><React.Fragment key={k}><label>{k.replaceAll("_"," ")}</label><input required value={payrollForm[k]} onChange={e=>setPayrollForm({...payrollForm,[k]:e.target.value})}/></React.Fragment>)}<button className="primary">Generate payroll</button></form>}
  {section==="Leave policies"&&admin&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/leave-policies",{...policyForm,total_days_allowed:Number(policyForm.total_days_allowed)}),"Policy created");}}><h3>Create leave policy</h3><label>Leave type</label><select value={policyForm.leave_type} onChange={e=>setPolicyForm({...policyForm,leave_type:e.target.value})}><option>SICK</option><option>CASUAL</option><option>PAID</option></select><label>Allowed days</label><input type="number" min="0" value={policyForm.total_days_allowed} onChange={e=>setPolicyForm({...policyForm,total_days_allowed:e.target.value})}/><button className="primary">Save policy</button></form>}
  </main></div>;
}

export default function App() {
  const [user,setUser]=useState(null);
  const [checking,setChecking]=useState(Boolean(localStorage.getItem("worksphere_token")));
  async function login(u){setUser(u);}
  useEffect(()=>{if(localStorage.getItem("worksphere_token")) api.get("/auth/me").then(r=>setUser(r.data)).catch(()=>localStorage.removeItem("worksphere_token")).finally(()=>setChecking(false));},[]);
  function logout(){localStorage.removeItem("worksphere_token");setUser(null);}
  if(checking) return <p className="loading">Loading WorkSphere…</p>;
  return user ? <Dashboard user={user} onLogout={logout}/> : <Auth onLogin={login}/>;
}
