
import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .database import get_db
from .models import Employee, User
from .security import require_roles

router = APIRouter(prefix="/employees", tags=["Employee CSV"])


@router.post("/import/csv")
async def import_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("HR", "ADMIN")),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    try:
        content = await file.read()
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

        required = {
            "id", "full_name", "designation",
            "department", "salary", "status"
        }

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
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
                name = row["full_name"].strip()

                if salary < 0 or not name:
                    raise ValueError("Invalid name or salary")

                user = db.get(User, user_id)
                if not user:
                    skipped += 1
                    continue

                existing = db.query(Employee).filter(
                    Employee.user_id == user_id
                ).first()

                if existing:
                    skipped += 1
                    continue

                db.add(Employee(
                    user_id=user_id,
                    full_name=name,
                    designation=row["designation"].strip(),
                    department=row["department"].strip(),
                    salary=salary,
                    status=row["status"].strip().upper(),
                ))
                imported += 1

            except (ValueError, TypeError, KeyError):
                raise HTTPException(
                    status_code=400,
                    detail="CSV contains an invalid employee row. No records were imported.",
                )

        db.commit()
        return {
            "message": "CSV import completed",
            "imported": imported,
            "skipped": skipped,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to process CSV file.")
    finally:
        await file.close()
