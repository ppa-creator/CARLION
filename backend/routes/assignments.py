from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.assignment import DriverVehicleAssignment
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.schemas.assignment import AssignmentCreate, AssignmentRead

router = APIRouter(prefix="/assignments", tags=["assignments"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=AssignmentRead)
def create_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    
    # 🔍 kontrola vodiča
    driver = db.query(Driver).filter(Driver.id == assignment.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # 🔍 kontrola vozidla
    vehicle = db.query(Vehicle).filter(Vehicle.id == assignment.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # 🔍 kontrola duplicity (aktívne priradenie)
    existing = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.driver_id == assignment.driver_id,
        DriverVehicleAssignment.vehicle_id == assignment.vehicle_id,
        DriverVehicleAssignment.assigned_to == None
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Assignment already exists for this driver and vehicle"
        )

    # 🔍 kontrola primary vozidla
    if assignment.is_primary:
        existing_primary = db.query(DriverVehicleAssignment).filter(
            DriverVehicleAssignment.driver_id == assignment.driver_id,
            DriverVehicleAssignment.is_primary == True,
            DriverVehicleAssignment.assigned_to == None
        ).first()
    
        if existing_primary:
            raise HTTPException(
                status_code=400,
                detail="Driver already has a primary vehicle"
            )

    db_assignment = DriverVehicleAssignment(
        driver_id=assignment.driver_id,
        vehicle_id=assignment.vehicle_id,
        assigned_from=assignment.assigned_from,
        assigned_to=assignment.assigned_to,
        is_primary=assignment.is_primary,
        note=assignment.note,
    )

    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


@router.get("", response_model=list[AssignmentRead])
def list_assignments(db: Session = Depends(get_db)):
    return db.query(DriverVehicleAssignment).all()