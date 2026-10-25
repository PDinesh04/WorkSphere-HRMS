# WorkSphere HRMS (Phase 1 + Phase 2 starter)

## Requirements
- Python 3.10+
- Node.js 18+
- VS Code

## 1. Backend setup (PowerShell)
Open a terminal in `WorkSphere/backend`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace `SECRET_KEY` with a random secret of at least 32 characters. Example generation:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Copy the generated value into `.env`.

Start the API:
```powershell
python -m uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## 2. Frontend setup
Open a second terminal in `WorkSphere/frontend`:
```powershell
npm install
npm run dev
```
Open the URL Vite prints, normally http://localhost:5173.

## 3. First user / admin role
Register the first user in the UI. All public registrations are EMPLOYEE for security. To make the first user an ADMIN for local development, stop the backend and run this from `WorkSphere/backend` with the venv active, after registering:
```powershell
python -c "from app.database import SessionLocal; from app.models import User; db=SessionLocal(); u=db.query(User).filter_by(username='YOUR_USERNAME').first(); print('User not found' if not u else 'Current role: '+u.role); u.role='ADMIN' if u else None; db.commit() if u else None; db.close()"
```
Replace `YOUR_USERNAME` with the registered username, restart the backend, then sign out/in to refresh the JWT. Do not expose this development workflow in production.

## Included modules
- JWT authentication, password hashing, active user checks
- Employee profiles and HR/Admin employee list/update
- Attendance check-in/check-out with one record per employee/day
- Leave requests, HR/Admin approval, balances and policy endpoints
- Payroll generation and employee-owned payroll history
- Notifications, dashboard KPI endpoint
- Admin user role assignment and deactivation
- React login/register and basic self-service/HR/admin views

## Important limitations
This is a learning starter, not a production-certified payroll or HR system. It uses SQLite and `create_all` rather than migrations. Leave counting currently uses calendar days, not working days or holidays. Automatic absent marking, late-entry rules, overtime, payslip PDF generation, audit logs, password reset, refresh tokens, and robust production deployment still need implementation/testing. Configure backups, TLS, secrets, migrations, audit controls, and legal payroll rules before real use.
