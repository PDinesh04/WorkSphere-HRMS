# WorkSphere – HR Management System (HRMS)

## Project Overview
WorkSphere is a full-stack Human Resource Management System designed to simplify employee management and HR operations.

## Features
- User registration and login using JWT authentication
- Role-based access control for Employee, HR, and Admin
- Employee management and search
- Attendance check-in and check-out
- Leave requests and approvals
- Payroll management
- Shift management and assignments
- Employee document uploads
- Notifications and performance reviews
- Reports and analytics
- CSV employee import and export

## Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- JWT authentication

### Frontend
- React
- Vite
- JavaScript
- Axios
- CSS

## Project Structure

```text
WorkSphere/
├── backend/
│   ├── app/
│   ├── employees.csv
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    ├── package.json
    └── index.html
```

## Setup Instructions

### 1. Backend

Open a terminal in the `backend` directory.

Activate your virtual environment in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload
```

Backend API documentation:

http://127.0.0.1:8000/docs

### 2. Frontend

Open a second terminal in the `frontend` directory.

Install dependencies:

```powershell
npm install
```

Start the frontend:

```powershell
npm run dev
```

Open the local URL printed by Vite, usually:

http://localhost:5173/

## Security Notes
- Keep `.env` and secret keys private.
- Do not commit passwords, tokens, virtual environments, or database files containing sensitive data.
- Change temporary passwords before using the application outside local testing.
- Configure a strong secret key for JWT authentication.

## Future Improvements
- Automated testing
- Improved dashboard visualizations
- Password reset functionality
- Deployment to a production server

## Author
WorkSphere HRMS Project
