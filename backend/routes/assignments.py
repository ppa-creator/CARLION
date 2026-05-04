from datetime import date

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


def _range_overlaps(
    left_from: date | None,
    left_to: date | None,
    right_from: date | None,
    right_to: date | None,
) -> bool:
    left_start = left_from or date.min
    left_end = left_to or date.max
    right_start = right_from or date.min
    right_end = right_to or date.max

    return left_start <= right_end and right_start <= left_end


def _validate_assignment_dates(assigned_from: date | None, assigned_to: date | None) -> None:
    if assigned_from and assigned_to and assigned_from > assigned_to:
        raise HTTPException(status_code=400, detail="assigned_from cannot be after assigned_to")


def _check_assignment_conflicts(
    db: Session,
    driver_id: int,
    vehicle_id: int,
    assigned_from: date | None,
    assigned_to: date | None,
    is_primary: bool,
    exclude_assignment_id: int | None = None,
) -> None:
    driver_assignments = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.driver_id == driver_id
    ).all()

    for item in driver_assignments:
        if exclude_assignment_id and item.id == exclude_assignment_id:
            continue

        if _range_overlaps(assigned_from, assigned_to, item.assigned_from, item.assigned_to):
            raise HTTPException(
                status_code=400,
                detail="Driver already has an assignment in the selected period"
            )

    vehicle_assignments = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.vehicle_id == vehicle_id
    ).all()

    for item in vehicle_assignments:
        if exclude_assignment_id and item.id == exclude_assignment_id:
            continue

        if _range_overlaps(assigned_from, assigned_to, item.assigned_from, item.assigned_to):
            raise HTTPException(
                status_code=400,
                detail="Vehicle is already assigned in the selected period"
            )

    if is_primary:
        primary_assignments = db.query(DriverVehicleAssignment).filter(
            DriverVehicleAssignment.driver_id == driver_id,
            DriverVehicleAssignment.is_primary == True
        ).all()

        for item in primary_assignments:
            if exclude_assignment_id and item.id == exclude_assignment_id:
                continue

            if _range_overlaps(assigned_from, assigned_to, item.assigned_from, item.assigned_to):
                raise HTTPException(
                    status_code=400,
                    detail="Driver already has a primary vehicle in the selected period"
                )


@router.post("", response_model=AssignmentRead)
def create_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    _validate_assignment_dates(assignment.assigned_from, assignment.assigned_to)

    # Driver must exist.
    driver = db.query(Driver).filter(Driver.id == assignment.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Vehicle must exist.
    vehicle = db.query(Vehicle).filter(Vehicle.id == assignment.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    _check_assignment_conflicts(
        db=db,
        driver_id=assignment.driver_id,
        vehicle_id=assignment.vehicle_id,
        assigned_from=assignment.assigned_from,
        assigned_to=assignment.assigned_to,
        is_primary=assignment.is_primary,
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


@router.get("/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    db_assignment = db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.id == assignment_id).first()

    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return db_assignment


@router.put("/{assignment_id}", response_model=AssignmentRead)
def update_assignment(assignment_id: int, assignment: AssignmentCreate, db: Session = Depends(get_db)):
    db_assignment = db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.id == assignment_id).first()

    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    _validate_assignment_dates(assignment.assigned_from, assignment.assigned_to)

    driver = db.query(Driver).filter(Driver.id == assignment.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    vehicle = db.query(Vehicle).filter(Vehicle.id == assignment.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    _check_assignment_conflicts(
        db=db,
        driver_id=assignment.driver_id,
        vehicle_id=assignment.vehicle_id,
        assigned_from=assignment.assigned_from,
        assigned_to=assignment.assigned_to,
        is_primary=assignment.is_primary,
        exclude_assignment_id=assignment_id,
    )

    db_assignment.driver_id = assignment.driver_id
    db_assignment.vehicle_id = assignment.vehicle_id
    db_assignment.assigned_from = assignment.assigned_from
    db_assignment.assigned_to = assignment.assigned_to
    db_assignment.is_primary = assignment.is_primary
    db_assignment.note = assignment.note

    db.commit()
    db.refresh(db_assignment)
    return db_assignment


@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    db_assignment = db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.id == assignment_id).first()

    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(db_assignment)
    db.commit()

    return {"message": "Assignment deleted successfully"}