
import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee, User
from app.dependencies import require_roles

router = APIRouter(prefix="/employees", tags=["Employee CSV"])


@router.post("/import/csv")
async def import_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("HR", "ADMIN")),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    try:
        content = await file.read()
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        required = {"id", "full_name", "designation", "department", "salary", "status"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise HTTPException(
                status_code=400,
                detail="CSV must contain: id, full_name, designation, department, salary, status",
            )

        imported = 0
        skipped = 0

        for row in reader:
            try:
                user_id = int(row["id"])
                salary = float(row["salary"])
                user = db.query(User).filter(User.id == user_id).first()

                if not user:
                    skipped += 1
                    continue

                existing = db.query(Employee).filter(
                    Employee.user_id == user_id
                ).first()

                if existing:
                    skipped += 1
                    continue

                employee = Employee(
                    user_id=user_id,
                    full_name=row["full_name"].strip(),
                    designation=row["designation"].strip(),
                    department=row["department"].strip(),
                    salary=salary,
                    status=row["status"].strip().upper() or "ACTIVE",
                )

                db.add(employee)
                imported += 1

            except (ValueError, TypeError, KeyError):
                skipped += 1

        db.commit()
        return {"imported": imported, "skipped": skipped}

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="CSV import failed. Check the CSV format and database.",
        ) from exc
    finally:
        await file.close()
