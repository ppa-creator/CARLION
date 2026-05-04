from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.driver import Driver
from backend.models.assignment import DriverVehicleAssignment
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


@router.delete("/{driver_id}")
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    db_driver = db.query(Driver).filter(Driver.id == driver_id).first()

    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    existing_assignment = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.driver_id == driver_id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=400,
            detail="Driver has assignments and cannot be deleted"
        )

    db.delete(db_driver)
    db.commit()

    return {"message": "Driver deleted successfully"}


@router.post("/{driver_id}/deactivate")
def deactivate_driver(driver_id: int, db: Session = Depends(get_db)):
    db_driver = db.query(Driver).filter(Driver.id == driver_id).first()

    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    active_assignments = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.driver_id == driver_id,
        DriverVehicleAssignment.assigned_to == None
    ).all()

    today = date.today()

    for assignment in active_assignments:
        assignment.assigned_to = today

    db_driver.is_active = False

    db.commit()

    return {"message": "Driver deactivated and assignments closed"}


@router.get("", response_model=list[DriverRead])
def list_drivers(db: Session = Depends(get_db)):
    return db.query(Driver).filter(Driver.is_active == True).all()


@router.put("/{driver_id}", response_model=DriverRead)
def update_driver(driver_id: int, driver: DriverCreate, db: Session = Depends(get_db)):
    db_driver = db.query(Driver).filter(Driver.id == driver_id).first()

    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    db_driver.first_name = driver.first_name
    db_driver.last_name = driver.last_name
    db_driver.phone = driver.phone
    db_driver.email = driver.email
    db_driver.license_number = driver.license_number
    db_driver.license_valid_until = driver.license_valid_until
    db_driver.note = driver.note

    db.commit()
    db.refresh(db_driver)
    return db_driver