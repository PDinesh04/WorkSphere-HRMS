# WorkSphere – HR Management System (HRMS)

## Project Overview
WorkSphere is a full-stack Human Resources Management System designed to manage employees, attendance, leave requests, payroll, performance reviews, documents, and HR operations.

## Technology Stack
- **Backend:** Python, FastAPI
- **Frontend:** React, Vite, Axios
- **Database:** SQLite
- **Authentication:** JWT
- **API Testing:** Swagger UI

## Features

### Core HR Management
- User registration and login
- Role-based access control for Employee, HR, and Admin
- Employee profile management
- Attendance check-in and check-out
- Leave requests, approvals, and leave policies
- Payroll generation and records
- Notifications and dashboards

### Advanced HR Features
- Shift creation and employee shift assignments
- Automated attendance and absence marking
- Leave calendar and team view
- Employee document upload and download
- Performance reviews and ratings
- Analytics and department reports
- Advanced employee search and filtering

## Project Structure

```text
WorkSphere/
├── backend/
│   ├── app/
│   ├── private_documents/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
└── README.md
```

## Running the Project

### 1. Start the Backend

Open a terminal in VS Code:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend API: http://127.0.0.1:8000

Swagger documentation: http://127.0.0.1:8000/docs

### 2. Start the Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL shown in the terminal, usually http://localhost:5173.

## Security
- JWT-based authentication
- Role-based authorization
- Input validation
- Secure handling of uploaded documents

**Important:** Do not commit passwords, secret keys, access tokens, database credentials, or private employee documents to GitHub.

## Repository
https://github.com/PDinesh04/WorkSphere-HRMS

## Project Status
Phase 1, Phase 2, and Phase 3 features have been implemented and tested in the local development environment. Further testing and deployment configuration may be required before production use.
