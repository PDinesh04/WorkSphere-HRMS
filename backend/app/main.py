from datetime import date, datetime, time, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func
from .database import Base, engine, get_db
from . import models, schemas
from .security import hash_password, verify_password, create_access_token, get_current_user, require_roles

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
Base.metadata.create_all(bind=engine)
app = FastAPI(title="WorkSphere HRMS API", version="1.0.0",
              description="Phase 1 and Phase 2 HRMS starter API")



app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



def notify(db: Session, user_id: int, title: str, message: str):
    db.add(models.Notification(user_id=user_id, title=title, message=message))

def employee_for_user(db: Session, user: models.User):
    emp = db.query(models.Employee).filter_by(user_id=user.id).first()
    if not emp:
        raise HTTPException(404, "Employee profile not found for this user")
    return emp

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
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.username == form_data.username)
        .first()
    )

    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
    }


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
    db.commit(); db.refresh(emp)
    return emp

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
    if not record:
        record = models.Attendance(employee_id=emp.id, date=today, check_in=now, status="PRESENT")
        db.add(record)
    else:
        record.check_in = now
        record.status = "PRESENT"
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
