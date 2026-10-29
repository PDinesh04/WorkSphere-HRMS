from datetime import date, datetime, time, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
import csv
import io
from fastapi.responses import StreamingResponse

from app.analytics_routes import router as analytics_router
from app import settlement_models
from app.settlement_routes import router as settlement_router
from app import exit_models
from app.exit_routes import router as exit_router
from app import resignation_models
from app.resignation_routes import router as resignation_router
from app.onboarding_routes import router as onboarding_router
from app import onboarding_models
from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import audit_models
from app.audit_routes import router as audit_router
from app.employee_csv import router as employee_csv_router

from app import settings_models
from app.settings_routes import router as settings_router
from sqlalchemy import func, or_
import os, uuid, shutil
from apscheduler.schedulers.background import BackgroundScheduler
from .database import Base, engine, get_db, SessionLocal
from . import models, schemas
from .security import hash_password, verify_password, create_access_token, get_current_user, require_roles
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WorkSphere HRMS API",
    version="1.0.0",
    description="WorkSphere HRMS Phase 1–3 API"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

from app.employee_csv import router as employee_csv_router
app.include_router(employee_csv_router)
app.include_router(onboarding_router)
app.include_router(employee_csv_router)
def _mark_absences(db: Session, now: datetime):
    today = now.date(); created = 0
    for assignment in db.query(models.EmployeeShift).all():
        shift = db.get(models.Shift, assignment.shift_id)
        emp = db.get(models.Employee, assignment.employee_id)
        if not shift or not emp: continue
        sh, sm = map(int, shift.start_time.split(":"))
        eh, em = map(int, shift.end_time.split(":"))
        overnight = (eh, em) <= (sh, sm)
        candidate_dates = [today]
        if overnight: candidate_dates.append(today - timedelta(days=1))
        for shift_date in candidate_dates:
            end_date = shift_date + timedelta(days=1) if overnight else shift_date
            shift_end = datetime.combine(end_date, time(eh, em))
            if shift_end > now: continue
            existing = db.query(models.Attendance).filter_by(employee_id=emp.id, date=shift_date).first()
            if existing is None:
                db.add(models.Attendance(employee_id=emp.id, date=shift_date, status="ABSENT"))
                db.add(models.Notification(user_id=emp.user_id, title="Attendance marked absent", message=f"No check-in was recorded for your {shift.name} shift on {shift_date.isoformat()}."))
                created += 1
            record_audit(
    db,
    user,
    "ATTENDANCE_RECORDED",
    f"Attendance recorded for employee ID {data.employee_id}",
)
    record_audit(
    db,
    user,
    "ATTENDANCE_CHECK_IN",
    f"Employee {emp.full_name} checked in",
    )
    record_audit(
    db,
    user,
    "ATTENDANCE_CHECK_OUT",
    f"Employee {emp.full_name} checked out",
    )
    db.commit()
    return created
app.include_router(resignation_router)
app.include_router(exit_router)
app.include_router(settlement_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(audit_router)
def _scheduled_absence_job():
    db = SessionLocal()
    try:
        _mark_absences(db, datetime.now())
    except Exception:
        db.rollback()
    finally:
        db.close()

_scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_automation_scheduler():
    if not _scheduler.running:
        _scheduler.add_job(_scheduled_absence_job, "cron", hour=23, minute=59, id="daily_absence", replace_existing=True)
        _scheduler.start()

@app.on_event("shutdown")
def stop_automation_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)

def notify(db: Session, user_id: int, title: str, message: str):
    db.add(models.Notification(user_id=user_id, title=title, message=message))


def record_audit(
    db: Session,
    user: models.User,
    action: str,
    details: str = "",
):
    from app.audit_models import AuditLog

    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action=action,
        details=details,
    )

    db.add(log)
def employee_for_user(db: Session, user: models.User):
    emp = db.query(models.Employee).filter_by(user_id=user.id).first()
    if not emp:
        raise HTTPException(404, "Employee profile not found for this user")
    return emp
@app.get("/employees/export/csv")
def export_employees_csv(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    employees = (
        db.query(models.Employee)
        .order_by(models.Employee.id)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Employee ID",
        "User ID",
        "Full Name",
        "Department",
        "Designation",
        "Salary",
        "Joining Date",
        "Status",
    ])

    for emp in employees:
        writer.writerow([
            emp.id,
            emp.user_id,
            emp.full_name,
            emp.department,
            emp.designation,
            emp.salary,
            emp.joining_date,
            emp.status,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="worksphere_employees.csv"'
        },
    )

@app.get("/")
def home():
    return {"message": "Welcome to WorkSphere HRMS", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter((models.User.username == data.username) | (models.User.email == data.email)).first():
        raise HTTPException(409, "Username or email already exists")
    user = models.User(username=data.username, email=str(data.email),
                       hashed_password=hash_password(data.password), role="EMPLOYEE")
    db.add(user)
    db.flush()
    employee = models.Employee(user_id=user.id, full_name=data.full_name)
    db.add(employee)
    db.flush()
    for policy in db.query(models.LeavePolicy).all():
        db.add(models.LeaveBalance(employee_id=employee.id, leave_type=policy.leave_type,
                                   remaining_days=policy.total_days_allowed))
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login")
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password")
    if not user.is_active:
        raise HTTPException(403, "Account is inactive")
    return {"access_token": create_access_token(user), "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "role": user.role}}

@app.post("/auth/token", include_in_schema=False)
def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password")
    if not user.is_active:
        raise HTTPException(403, "Account is inactive")
    return {"access_token": create_access_token(user), "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user

@app.get("/employees")
def list_employees(q: str = "", department: str = "", db: Session = Depends(get_db),
                   user: models.User = Depends(require_roles("HR", "ADMIN"))):
    query = db.query(models.Employee)
    if q:
        query = query.filter(models.Employee.full_name.ilike(f"%{q}%"))
    if department:
        query = query.filter(models.Employee.department == department)
    return query.order_by(models.Employee.id.desc()).all()

@app.post("/employees", status_code=201)
def create_employee(data: schemas.EmployeeIn, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("HR", "ADMIN"))):
    account = db.get(models.User, data.user_id)
    if not account:
        raise HTTPException(404, "User not found")
    if db.query(models.Employee).filter_by(user_id=data.user_id).first():
        raise HTTPException(409, "User already has an employee profile")
    values = data.model_dump()
    values["joining_date"] = values["joining_date"] or date.today()
    emp = models.Employee(**values)
    db.add(emp); db.flush()
    for policy in db.query(models.LeavePolicy).all():
        db.add(models.LeaveBalance(employee_id=emp.id, leave_type=policy.leave_type,
                                   remaining_days=policy.total_days_allowed))
    record_audit(
        db,
        user,
        "EMPLOYEE_CREATED",
        f"Created employee profile for {emp.full_name}",
    )

    db.commit()
    db.refresh(emp)
    return emp

@app.post("/employees/import/csv")
def import_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(415, "Please upload a CSV file")

    try:
        content = file.file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required = {
            "user_id", "full_name", "designation",
            "department", "salary", "status",
        }

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise HTTPException(422, "Invalid CSV headers")

        rows = list(reader)
        created = 0

        for row in rows:
            user_id = int(row["user_id"])
            name = row["full_name"].strip()
            salary = float(row["salary"])
            status = row["status"].strip().upper()

            if not name or salary < 0:
                raise HTTPException(422, "Invalid name or salary")

            if status not in ("ACTIVE", "INACTIVE"):
                raise HTTPException(422, "Invalid employee status")

            if not db.get(models.User, user_id):
                raise HTTPException(422, f"User ID {user_id} not found")

            if db.query(models.Employee).filter_by(user_id=user_id).first():
                raise HTTPException(
                    409, f"User ID {user_id} already has an employee profile"
                )

            employee = models.Employee(
                user_id=user_id,
                full_name=name,
                designation=row["designation"].strip(),
                department=row["department"].strip(),
                salary=salary,
                status=status,
            )
            db.add(employee)
            db.flush()

            for policy in db.query(models.LeavePolicy).all():
                db.add(models.LeaveBalance(
                    employee_id=employee.id,
                    leave_type=policy.leave_type,
                    remaining_days=policy.total_days_allowed,
                ))

            record_audit(
                db, user, "EMPLOYEE_IMPORTED",
                f"Imported employee profile for {name}",
            )
            created += 1

        db.commit()
        return {"message": "CSV import completed", "created": created}

    except Exception:
        db.rollback()
        raise
    finally:
        file.file.close()
@app.patch("/employees/{employee_id}")
def update_employee(employee_id: int, data: schemas.EmployeeUpdate, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("HR", "ADMIN"))):
    emp = db.get(models.Employee, employee_id)
    if not emp: raise HTTPException(404, "Employee not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(emp, key, value)
    db.commit(); db.refresh(emp)
    return emp

@app.get("/employees/me")
def my_profile(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    return {"user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role},
            "employee": emp}

@app.get("/attendance")
def attendance_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role in ("HR", "ADMIN"):
        return db.query(models.Attendance).order_by(models.Attendance.date.desc()).all()
    emp = employee_for_user(db, user)
    return db.query(models.Attendance).filter_by(employee_id=emp.id).order_by(models.Attendance.date.desc()).all()

@app.post("/attendance/check-in")
def check_in(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    today = date.today()
    record = db.query(models.Attendance).filter_by(employee_id=emp.id, date=today).first()
    if record and record.check_in:
        raise HTTPException(409, "Already checked in today")
    now = datetime.now()
    assignment = db.query(models.EmployeeShift).filter_by(employee_id=emp.id).first()
    status = "PRESENT"
    if assignment:
        shift = db.get(models.Shift, assignment.shift_id)
        if shift:
            start_hour, start_minute = map(int, shift.start_time.split(":"))
            shift_start = datetime.combine(today, time(start_hour, start_minute))
            if now > shift_start + timedelta(minutes=10):
                status = "LATE"
                notify(db, user.id, "Late attendance", f"Your check-in was after the 10-minute grace period for {shift.name} shift.")
    if not record:
        record = models.Attendance(employee_id=emp.id, date=today, check_in=now, status=status)
        db.add(record)
    else:
        record.check_in = now
        record.status = status
    db.commit(); db.refresh(record)
    return record

@app.post("/attendance/check-out")
def check_out(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    record = db.query(models.Attendance).filter_by(employee_id=emp.id, date=date.today()).first()
    if not record or not record.check_in:
        raise HTTPException(400, "Check in before checking out")
    if record.check_out:
        raise HTTPException(409, "Already checked out today")
    record.check_out = datetime.now()
    hours = (record.check_out - record.check_in).total_seconds() / 3600
    if hours < 4: record.status = "HALF_DAY"
    db.commit(); db.refresh(record)
    return {"attendance": record, "working_hours": round(hours, 2)}

@app.post("/leaves", status_code=201)
def apply_leave(data: schemas.LeaveIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if data.leave_type not in ("SICK", "CASUAL", "PAID"): raise HTTPException(422, "Invalid leave type")
    if data.end_date < data.start_date: raise HTTPException(422, "End date must not precede start date")
    emp = employee_for_user(db, user)
    days = (data.end_date - data.start_date).days + 1
    balance = db.query(models.LeaveBalance).filter_by(employee_id=emp.id, leave_type=data.leave_type).first()
    if balance and balance.remaining_days < days: raise HTTPException(400, "Insufficient leave balance")
    conflict = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.employee_id == emp.id,
        models.LeaveRequest.status.in_(["PENDING", "APPROVED"]),
        models.LeaveRequest.start_date <= data.end_date,
        models.LeaveRequest.end_date >= data.start_date,
    ).first()
    if conflict:
        raise HTTPException(409, "This leave overlaps an existing pending or approved request")
    item = models.LeaveRequest(employee_id=emp.id, **data.model_dump())
    db.add(item)
    for hr in db.query(models.User).filter(models.User.role.in_(["HR", "ADMIN"]), models.User.is_active == True).all():
        notify(db, hr.id, "Leave request", f"{emp.full_name} submitted a {data.leave_type} leave request.")
    db.commit(); db.refresh(item)
    return item

@app.get("/leaves")
def list_leaves(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    query = db.query(models.LeaveRequest)
    if user.role not in ("HR", "ADMIN"):
        emp = employee_for_user(db, user)
        query = query.filter_by(employee_id=emp.id)
    return query.order_by(models.LeaveRequest.created_at.desc()).all()

@app.patch("/leaves/{leave_id}/decision")
def decide_leave(leave_id: int, data: schemas.LeaveDecision, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("HR", "ADMIN"))):
    if data.status not in ("APPROVED", "REJECTED"): raise HTTPException(422, "Status must be APPROVED or REJECTED")
    item = db.get(models.LeaveRequest, leave_id)
    if not item: raise HTTPException(404, "Leave request not found")
    if item.status != "PENDING": raise HTTPException(409, "Leave request has already been processed")
    emp = db.get(models.Employee, item.employee_id)
    if data.status == "APPROVED":
        days = (item.end_date - item.start_date).days + 1
        balance = db.query(models.LeaveBalance).filter_by(employee_id=item.employee_id, leave_type=item.leave_type).first()
        if balance:
            if balance.remaining_days < days: raise HTTPException(400, "Insufficient leave balance")
            balance.remaining_days -= days
    item.status = data.status
    notify(db, emp.user_id, "Leave update", f"Your leave request was {data.status.lower()}.")
    db.commit(); db.refresh(item)
    return item

@app.get("/leave-balances")
def leave_balances(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role in ("HR", "ADMIN"):
        return db.query(models.LeaveBalance).all()
    emp = employee_for_user(db, user)
    return db.query(models.LeaveBalance).filter_by(employee_id=emp.id).all()

@app.get("/leave-policies")
def policies(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.LeavePolicy).all()

@app.post("/leave-policies", status_code=201)
def create_policy(data: schemas.PolicyIn, db: Session = Depends(get_db),
                  user: models.User = Depends(require_roles("ADMIN"))):
    policy = db.query(models.LeavePolicy).filter_by(leave_type=data.leave_type).first()
    if policy: raise HTTPException(409, "Policy already exists")
    policy = models.LeavePolicy(**data.model_dump())
    db.add(policy)
    db.flush()
    for emp in db.query(models.Employee).all():
        db.add(models.LeaveBalance(employee_id=emp.id, leave_type=policy.leave_type,
                                   remaining_days=policy.total_days_allowed))
    db.commit(); db.refresh(policy)
    return policy

@app.post("/payroll", status_code=201)
def generate_payroll(data: schemas.PayrollIn, db: Session = Depends(get_db),
                     user: models.User = Depends(require_roles("HR", "ADMIN"))):
    emp = db.get(models.Employee, data.employee_id)
    if not emp: raise HTTPException(404, "Employee not found")
    if db.query(models.Payroll).filter_by(employee_id=data.employee_id, month=data.month).first():
        raise HTTPException(409, "Payroll already exists for this employee and month")
    values = data.model_dump()
    values["net_salary"] = round(data.basic_salary + data.allowances + data.bonus - data.deductions, 2)
    item = models.Payroll(**values)
    db.add(item)
    notify(db, emp.user_id, "Payroll generated", f"Payroll for {data.month} is available.")
    db.commit(); db.refresh(item)
    return item

@app.get("/payroll")
def payroll_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    query = db.query(models.Payroll)
    if user.role not in ("HR", "ADMIN"):
        emp = employee_for_user(db, user)
        query = query.filter_by(employee_id=emp.id)
    return query.order_by(models.Payroll.month.desc()).all()

@app.get("/notifications")
def notifications(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Notification).filter_by(user_id=user.id).order_by(models.Notification.created_at.desc()).all()

@app.patch("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db),
                           user: models.User = Depends(get_current_user)):
    item = db.query(models.Notification).filter_by(id=notification_id, user_id=user.id).first()
    if not item: raise HTTPException(404, "Notification not found")
    item.is_read = True
    db.commit(); return {"message": "Marked as read"}

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: models.User = Depends(require_roles("HR", "ADMIN"))):
    return {
        "total_employees": db.query(models.Employee).count(),
        "active_employees": db.query(models.Employee).filter_by(status="ACTIVE").count(),
        "present_today": db.query(models.Attendance).filter_by(date=date.today(), status="PRESENT").count(),
        "pending_leaves": db.query(models.LeaveRequest).filter_by(status="PENDING").count(),
        "payroll_this_month": db.query(models.Payroll).filter_by(month=date.today().strftime("%Y-%m")).count(),
    }

@app.get("/admin/users")
def admin_users(db: Session = Depends(get_db), user: models.User = Depends(require_roles("ADMIN"))):
    return db.query(models.User).order_by(models.User.id).all()

@app.patch("/admin/users/{user_id}")
def update_user(user_id: int, data: schemas.RoleUpdate, db: Session = Depends(get_db),
                user: models.User = Depends(require_roles("ADMIN"))):
    if data.role not in ("EMPLOYEE", "HR", "ADMIN"): raise HTTPException(422, "Invalid role")
    target = db.get(models.User, user_id)
    if not target: raise HTTPException(404, "User not found")
    if target.id == user.id and (data.role != "ADMIN" or not data.is_active):
        raise HTTPException(400, "You cannot remove your own admin access or deactivate yourself")
    target.role = data.role
    target.is_active = data.is_active
    db.commit(); db.refresh(target)
    return {"id": target.id, "username": target.username, "role": target.role, "is_active": target.is_active}

@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("ADMIN"))):
    target = db.get(models.User, user_id)
    if not target: raise HTTPException(404, "User not found")
    if target.id == user.id: raise HTTPException(400, "You cannot delete your own account")
    # Keep historical HR records; deactivate rather than cascading deletion.
    target.is_active = False
    db.commit()
    return {"message": "User deactivated"}


# ---------------- Phase 3: shifts and attendance automation ----------------
@app.get("/shifts")
def list_shifts(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Shift).order_by(models.Shift.start_time).all()

@app.post("/shifts", status_code=201)
def create_shift(data: schemas.ShiftIn, db: Session = Depends(get_db), user: models.User = Depends(require_roles("ADMIN"))):
    if data.start_time == data.end_time:
        raise HTTPException(422, "Shift start and end times must differ")
    if db.query(models.Shift).filter_by(name=data.name.strip()).first():
        raise HTTPException(409, "A shift with this name already exists")
    item = models.Shift(name=data.name.strip(), start_time=data.start_time, end_time=data.end_time)
    db.add(item); db.commit(); db.refresh(item); return item

@app.get("/employee-shifts")
def list_employee_shifts(db: Session = Depends(get_db), user: models.User = Depends(require_roles("HR", "ADMIN"))):
    rows = db.query(models.EmployeeShift, models.Employee, models.Shift).join(models.Employee, models.EmployeeShift.employee_id == models.Employee.id).join(models.Shift, models.EmployeeShift.shift_id == models.Shift.id).all()
    return [{"id": a.id, "employee_id": e.id, "employee_name": e.full_name, "shift_id": sh.id, "shift_name": sh.name, "start_time": sh.start_time, "end_time": sh.end_time} for a,e,sh in rows]

@app.get("/employee-shifts/me")
def my_shift(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    assignment = db.query(models.EmployeeShift).filter_by(employee_id=emp.id).first()
    if not assignment: return {"assigned": False, "employee_id": emp.id, "employee_name": emp.full_name}
    shift = db.get(models.Shift, assignment.shift_id)
    return {"assigned": True, "employee_id": emp.id, "employee_name": emp.full_name, "shift_id": shift.id, "shift_name": shift.name, "start_time": shift.start_time, "end_time": shift.end_time}

@app.post("/employee-shifts", status_code=201)
def assign_shift(data: schemas.EmployeeShiftIn, db: Session = Depends(get_db), user: models.User = Depends(require_roles("HR", "ADMIN"))):
    if not db.get(models.Employee, data.employee_id): raise HTTPException(404, "Employee not found")
    if not db.get(models.Shift, data.shift_id): raise HTTPException(404, "Shift not found")
    assignment = db.query(models.EmployeeShift).filter_by(employee_id=data.employee_id).first()
    if assignment: assignment.shift_id = data.shift_id
    else:
        assignment = models.EmployeeShift(employee_id=data.employee_id, shift_id=data.shift_id); db.add(assignment)
    db.commit(); db.refresh(assignment); return assignment

@app.post("/automation/attendance/run")
def run_attendance_automation(db: Session = Depends(get_db), user: models.User = Depends(require_roles("ADMIN"))):
    """Idempotently mark assigned employees absent after their shift end for today."""
    now = datetime.now()
    created = _mark_absences(db, now)
    return {"date": now.date().isoformat(), "absent_records_created": created}

# ---------------- Module 15: leave calendar and team availability ----------------
@app.get("/leave-calendar")
def leave_calendar(start_date: date = Query(default=None), end_date: date = Query(default=None), db: Session = Depends(get_db), user: models.User = Depends(require_roles("HR", "ADMIN"))):
    start = start_date or date.today().replace(day=1)
    end = end_date or (start + timedelta(days=31))
    if end < start: raise HTTPException(422, "end_date must be on or after start_date")
    rows = db.query(models.LeaveRequest, models.Employee).join(models.Employee, models.LeaveRequest.employee_id == models.Employee.id).filter(models.LeaveRequest.status == "APPROVED", models.LeaveRequest.start_date <= end, models.LeaveRequest.end_date >= start).order_by(models.LeaveRequest.start_date).all()
    return [{"leave_id": l.id, "employee_id": e.id, "employee_name": e.full_name, "department": e.department, "leave_type": l.leave_type, "start_date": l.start_date, "end_date": l.end_date, "status": l.status} for l,e in rows]

# ---------------- Module 16: secure employee documents ----------------
DOCUMENT_DIR = Path(__file__).resolve().parents[1] / "private_documents"
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_DOCUMENT_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx"}
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024

@app.get("/documents")
def list_documents(employee_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    query = db.query(models.EmployeeDocument)
    if user.role not in ("HR", "ADMIN"):
        emp = employee_for_user(db, user); query = query.filter_by(employee_id=emp.id)
    elif employee_id is not None:
        query = query.filter_by(employee_id=employee_id)
    return [{"id": d.id, "employee_id": d.employee_id, "file_name": d.file_name, "file_url": d.file_url, "uploaded_at": d.uploaded_at} for d in query.order_by(models.EmployeeDocument.uploaded_at.desc()).all()]

@app.post("/documents", status_code=201)
def upload_document(employee_id: int | None = None, file: UploadFile = File(...), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role not in ("HR", "ADMIN"):
        own_employee = employee_for_user(db, user)
        if employee_id is not None and own_employee.id != employee_id: raise HTTPException(403, "You can upload documents only to your own profile")
        employee_id = own_employee.id
    if employee_id is None: raise HTTPException(422, "employee_id is required for HR/Admin uploads")
    if not db.get(models.Employee, employee_id): raise HTTPException(404, "Employee not found")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCUMENT_TYPES: raise HTTPException(415, "Unsupported file type")
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    destination = DOCUMENT_DIR / stored_name
    size = 0
    try:
        with destination.open("wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_DOCUMENT_BYTES:
                    raise HTTPException(413, "Maximum document size is 10 MB")
                out.write(chunk)
        record = models.EmployeeDocument(employee_id=employee_id, file_name=Path(file.filename).name[:255], stored_name=stored_name, file_url="")
        db.add(record); db.commit(); db.refresh(record)
        record.file_url = f"/documents/{record.id}/download"
        db.commit(); db.refresh(record)
        return {"id": record.id, "employee_id": record.employee_id, "file_name": record.file_name, "file_url": record.file_url, "uploaded_at": record.uploaded_at}
    except Exception:
        if destination.exists(): destination.unlink()
        raise

@app.get("/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    record = db.get(models.EmployeeDocument, document_id)
    if not record: raise HTTPException(404, "Document not found")
    if user.role not in ("HR", "ADMIN") and employee_for_user(db, user).id != record.employee_id:
        raise HTTPException(403, "You cannot access this document")
    path = DOCUMENT_DIR / record.stored_name
    if not path.is_file(): raise HTTPException(404, "Document file is missing")
    return FileResponse(path, filename=record.file_name, media_type="application/octet-stream")

# ---------------- Module 17: performance reviews ----------------
@app.get("/performance")
def performance_reviews(employee_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    query = db.query(models.PerformanceReview)
    if user.role not in ("HR", "ADMIN"):
        emp = employee_for_user(db, user); query = query.filter_by(employee_id=emp.id)
    elif employee_id is not None:
        query = query.filter_by(employee_id=employee_id)
    return query.order_by(models.PerformanceReview.created_at.desc()).all()

@app.post("/performance", status_code=201)
def create_performance_review(data: schemas.PerformanceIn, db: Session = Depends(get_db), user: models.User = Depends(require_roles("HR", "ADMIN"))):
    if not db.get(models.Employee, data.employee_id): raise HTTPException(404, "Employee not found")
    item = models.PerformanceReview(**data.model_dump()); db.add(item)
    emp = db.get(models.Employee, data.employee_id)
    notify(db, emp.user_id, "Performance review added", f"A performance review for {data.review_period} is available.")
    db.commit(); db.refresh(item); return item

# ---------------- Module 18: analytics ----------------
@app.get("/analytics/summary")
def analytics_summary(start_date: date | None = None, end_date: date | None = None, department: str = "", db: Session = Depends(get_db), user: models.User = Depends(require_roles("HR", "ADMIN"))):
    if start_date and end_date and end_date < start_date: raise HTTPException(422, "end_date must be on or after start_date")
    employees_q = db.query(models.Employee)
    if department: employees_q = employees_q.filter(models.Employee.department == department)
    employees = employees_q.all(); ids = [e.id for e in employees]
    att_q = db.query(models.Attendance).filter(models.Attendance.employee_id.in_(ids)) if ids else db.query(models.Attendance).filter(False)
    leave_q = db.query(models.LeaveRequest).filter(models.LeaveRequest.employee_id.in_(ids)) if ids else db.query(models.LeaveRequest).filter(False)
    perf_q = db.query(models.PerformanceReview).filter(models.PerformanceReview.employee_id.in_(ids)) if ids else db.query(models.PerformanceReview).filter(False)
    if start_date: att_q=att_q.filter(models.Attendance.date >= start_date); leave_q=leave_q.filter(models.LeaveRequest.end_date >= start_date)
    if end_date: att_q=att_q.filter(models.Attendance.date <= end_date); leave_q=leave_q.filter(models.LeaveRequest.start_date <= end_date)
    attendance = att_q.all(); leaves = leave_q.all(); reviews = perf_q.all()
    by_department = []
    for dep in sorted({e.department or "Unassigned" for e in employees}):
        group = [e for e in employees if (e.department or "Unassigned") == dep]
        by_department.append({"department": dep, "employees": len(group), "active": sum(e.status == "ACTIVE" for e in group)})
    return {"employee_count": len(employees), "attendance_records": len(attendance), "present_records": sum(a.status in ("PRESENT", "LATE", "HALF_DAY") for a in attendance), "late_records": sum(a.status == "LATE" for a in attendance), "absent_records": sum(a.status == "ABSENT" for a in attendance), "leave_requests": len(leaves), "approved_leaves": sum(l.status == "APPROVED" for l in leaves), "pending_leaves": sum(l.status == "PENDING" for l in leaves), "average_performance_rating": round(sum(r.rating for r in reviews)/len(reviews), 2) if reviews else None, "performance_reviews": len(reviews), "departments": by_department}

# ---------------- Module 20: advanced employee search ----------------
@app.get("/employees/search")
def advanced_employee_search(q: str = "", department: str = "", role: str = "", status: str = "", attendance_status: str = "", min_rating: int | None = Query(default=None, ge=1, le=5), db: Session = Depends(get_db), user: models.User = Depends(require_roles("HR", "ADMIN"))):
    query = db.query(models.Employee).join(models.User, models.Employee.user_id == models.User.id)
    if q: query = query.filter(models.Employee.full_name.ilike(f"%{q}%"))
    if department: query = query.filter(models.Employee.department.ilike(f"%{department}%"))
    if role: query = query.filter(models.User.role == role.upper())
    if status: query = query.filter(models.Employee.status == status.upper())
    if attendance_status:
        today = date.today()
        query = query.join(models.Attendance, (models.Attendance.employee_id == models.Employee.id) & (models.Attendance.date == today)).filter(models.Attendance.status == attendance_status.upper())
    if min_rating is not None:
        query = query.filter(models.Employee.id.in_(db.query(models.PerformanceReview.employee_id).filter(models.PerformanceReview.rating >= min_rating)))
    rows = query.order_by(models.Employee.full_name).all()
    return [{"id": e.id, "user_id": e.user_id, "full_name": e.full_name, "designation": e.designation, "department": e.department, "joining_date": e.joining_date, "salary": e.salary, "status": e.status, "role": e.user.role} for e in rows]
