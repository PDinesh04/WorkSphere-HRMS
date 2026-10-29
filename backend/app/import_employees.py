
import csv
from datetime import date
from app.database import SessionLocal
from app.models import Employee, User
from app.security import hash_password

db = SessionLocal()

try:
    with open("employees.csv", "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            name = row["full_name"].strip()
            username = name.lower().replace(" ", "")
            email = username + "@example.com"

            # Find an existing user by username or email
            user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()

            # Create a new account if needed
            if not user:
                user = User(
                    username=username,
                    email=email,
                    hashed_password=hash_password("ChangeMe123!"),
                    role="EMPLOYEE"
                )
                db.add(user)
                db.flush()

                print(f"Created user account for {name}")

            # Avoid duplicate employee records
            existing = db.query(Employee).filter(
                Employee.user_id == user.id
            ).first()

            if existing:
                print(f"Skipping {name}: employee already exists.")
                continue

            employee = Employee(
                user_id=user.id,
                full_name=name,
                designation=row["designation"],
                department=row["department"],
                salary=float(row["salary"]),
                status=row["status"],
                joining_date=date.today()
            )

            db.add(employee)
            print(f"Added employee: {name}")

        db.commit()
        print("CSV import completed successfully.")

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
