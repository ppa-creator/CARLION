from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.driver import Driver
from backend.schemas.driver import DriverCreate, DriverRead

router = APIRouter(prefix="/drivers", tags=["drivers"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=DriverRead)
def create_driver(driver: DriverCreate, db: Session = Depends(get_db)):
    db_driver = Driver(
        first_name=driver.first_name,
        last_name=driver.last_name,
        phone=driver.phone,
        email=driver.email,
        license_number=driver.license_number,
        license_valid_until=driver.license_valid_until,
        note=driver.note,
    )
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@router.get("", response_model=list[DriverRead])
def list_drivers(db: Session = Depends(get_db)):
    return db.query(Driver).all()