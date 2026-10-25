import React, { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import api from "./api";

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
  const [payrollForm, setPayrollForm] = useState({ employee_id:"", month:new Date().toISOString().slice(0,7), basic_salary:"", allowances:"0", deductions:"0", bonus:"0" });
  const [policyForm, setPolicyForm] = useState({ leave_type:"CASUAL", total_days_allowed:12 });
  const [employeeForm, setEmployeeForm] = useState({ user_id:"", full_name:"", designation:"", department:"", salary:"0", status:"ACTIVE" });
  const [userList, setUserList] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const hr = ["HR","ADMIN"].includes(user.role), admin = user.role==="ADMIN";
  async function load() {
    try {
      if (section==="Overview") {
        if (hr) setDashboard((await api.get("/dashboard")).data);
        else setProfile((await api.get("/employees/me")).data);
      } else {
        const urls = { Employees:"/employees", Attendance:"/attendance", Leaves:"/leaves", Payroll:"/payroll", Notifications:"/notifications", "Leave balances":"/leave-balances", "Leave policies":"/leave-policies", "User management":"/admin/users" };
        if (urls[section]) {
          const result = await api.get(urls[section]); setData(result.data);
          if(section==="User management") setUserList(result.data);
        }
      }
    } catch(e) { setMessage(e.response?.data?.detail || "Could not load data. Check your permissions and backend."); }
  }
  useEffect(()=>{ load(); },[section]);
  async function act(fn, success) { setMessage(""); try { await fn(); setMessage(success); await load(); } catch(e) { setMessage(e.response?.data?.detail || "Action failed"); } }
  function list(items) {
    if (!items?.length) return <p className="muted">No records found.</p>;
    return <div className="tablewrap"><table><thead><tr>{Object.keys(items[0]).map(k=><th key={k}>{k.replaceAll("_"," ")}</th>)}{section==="Leaves"&&hr&&<th>Actions</th>}{section==="User management"&&admin&&<th>Role</th>}</tr></thead><tbody>{items.map((item,i)=><tr key={item.id??i}>{Object.entries(item).map(([k,v])=><td key={k}>{typeof v==="object"&&v!==null?JSON.stringify(v):String(v??"—")}</td>)}{section==="Leaves"&&hr&&<td>{item.status==="PENDING"&&<><button onClick={()=>act(()=>api.patch(`/leaves/${item.id}/decision`,{status:"APPROVED"}),"Leave approved")}>Approve</button> <button className="danger" onClick={()=>act(()=>api.patch(`/leaves/${item.id}/decision`,{status:"REJECTED"}),"Leave rejected")}>Reject</button></>}</td>}{section==="User management"&&admin&&<td><select value={item.role} onChange={e=>act(()=>api.patch(`/admin/users/${item.id}`,{role:e.target.value,is_active:item.is_active}),"User updated")}><option>EMPLOYEE</option><option>HR</option><option>ADMIN</option></select></td>}</tr>)}</tbody></table></div>;
  }
  const sections = ["Overview","My profile","Attendance","Leaves","Leave balances","Payroll","Notifications",...(hr?["Employees","Leave policies"]:[]),...(admin?["User management"]:[])];
  return <div className="layout"><aside><div className="brand smallbrand">W<span>S</span></div><h2>WorkSphere</h2><p className="muted">{user.username} · {user.role}</p>{sections.map(s=><button key={s} className={section===s?"nav active":"nav"} onClick={()=>{setSection(s);setMessage("");}}>{s}</button>)}<button className="nav logout" onClick={onLogout}>Sign out</button></aside>
  <main><header><div><p className="eyebrow">HUMAN RESOURCES</p><h1>{section}</h1></div><span className="role">{user.role}</span></header>
  {message&&<div className="notice">{message}</div>}
  {section==="Overview" && (hr ? dashboard ? <div className="cards">{Object.entries(dashboard).map(([k,v])=><div className="metric" key={k}><p>{k.replaceAll("_"," ")}</p><strong>{v}</strong></div>)}</div> : <p>Loading overview…</p> : <div className="panel"><h3>Welcome back, {user.username}</h3><p>Your self-service workspace is ready.</p>{profile&&<p>{profile.employee.full_name} · {profile.employee.department||"Department not set"}</p>}</div>)}
  {section==="My profile" && <div className="panel">{profile ? <pre>{JSON.stringify(profile,null,2)}</pre> : <button onClick={()=>act(async()=>setProfile((await api.get("/employees/me")).data),"Profile loaded")}>Load profile</button>}</div>}
  {["Employees","Attendance","Leaves","Leave balances","Payroll","Notifications","Leave policies","User management"].includes(section)&&list(data)}
  {section==="Attendance"&&<div className="actions"><button className="primary" onClick={()=>act(()=>api.post("/attendance/check-in"),"Checked in")}>Check in</button><button onClick={()=>act(()=>api.post("/attendance/check-out"),"Checked out")}>Check out</button></div>}
  {section==="Leaves"&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/leaves",leaveForm),"Leave request submitted");}}><h3>Apply for leave</h3><label>Type</label><select value={leaveForm.leave_type} onChange={e=>setLeaveForm({...leaveForm,leave_type:e.target.value})}><option>SICK</option><option>CASUAL</option><option>PAID</option></select><label>Start date</label><input type="date" required value={leaveForm.start_date} onChange={e=>setLeaveForm({...leaveForm,start_date:e.target.value})}/><label>End date</label><input type="date" required value={leaveForm.end_date} onChange={e=>setLeaveForm({...leaveForm,end_date:e.target.value})}/><label>Reason</label><textarea required value={leaveForm.reason} onChange={e=>setLeaveForm({...leaveForm,reason:e.target.value})}/><button className="primary">Submit leave request</button></form>}
  {section==="Employees"&&hr&&<form className="panel formgrid" onSubmit={e=>{e.preventDefault();act(()=>api.post("/employees",{...employeeForm,user_id:Number(employeeForm.user_id),salary:Number(employeeForm.salary)}),"Employee created");}}><h3>Add employee profile</h3>{Object.keys(employeeForm).map(k=><React.Fragment key={k}><label>{k.replaceAll("_"," ")}</label><input required={["user_id","full_name"].includes(k)} value={employeeForm[k]} onChange={e=>setEmployeeForm({...employeeForm,[k]:e.target.value})}/></React.Fragment>)}<button className="primary">Add employee</button><p className="muted small">Register the user's account first; use its user ID.</p></form>}
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
