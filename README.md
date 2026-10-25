# WorkSphere – HR Management System (HRMS)

WorkSphere is a full-stack Human Resource Management System designed to simplify employee management and HR operations through a web-based platform.

## Features

- **Authentication & Authorization:** User registration, login, JWT authentication, and role-based access for Admin, HR, and Employees.
- **Employee Management:** Create, view, search, and update employee records.
- **Attendance Management:** Employee check-in, check-out, and attendance history.
- **Leave Management:** Apply for leave, view requests, and approve or reject applications.
- **Payroll Management:** Generate payroll records and calculate net salary.
- **Notifications:** View notifications and mark them as read.
- **Dashboard:** View employee statistics, attendance, pending leaves, and payroll summaries.

## Technology Stack

**Frontend:** React, Vite, JavaScript, Axios

**Backend:** Python, FastAPI, SQLAlchemy

**Database:** SQLite

**Authentication:** JWT

**API Documentation:** Swagger UI

## Project Structure

```text
WorkSphere/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── database.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/PDinesh04/WorkSphere-HRMS.git
cd WorkSphere-HRMS
```

### 2. Set up the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory using `.env.example` as a template. Set a strong, random `SECRET_KEY` of at least 32 characters.

Start the backend:

```powershell
python -m uvicorn app.main:app --reload
```

Backend URL: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

### 3. Set up the frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually http://localhost:5173.

## Security Notes

- Never commit `.env` files, access tokens, passwords, or production secrets.
- Use a strong secret key for JWT authentication.
- Configure appropriate CORS origins before deploying.
- Configure production-grade database backups and migrations before production use.

## Future Improvements

- Automated attendance and absence tracking
- Payslip generation and downloadable reports
- Advanced reporting and analytics
- Password reset and account recovery
- Automated tests and database migrations
- Production deployment and monitoring

## Author

**Dinesh P**

GitHub: [PDinesh04](https://github.com/PDinesh04)

## Repository

[WorkSphere-HRMS on GitHub](https://github.com/PDinesh04/WorkSphere-HRMS)
