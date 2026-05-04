from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.assignment import DriverVehicleAssignment
from backend.models.vehicle import Vehicle
from backend.schemas.vehicle import VehicleCreate, VehicleRead

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=VehicleRead)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = Vehicle(
        license_plate=vehicle.license_plate,
        vin=vehicle.vin,
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year,
        fuel_type=vehicle.fuel_type,
        current_km=vehicle.current_km,
        note=vehicle.note,
    )
    db.add(db_vehicle)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Vehicle with this license plate or VIN already exists")

    db.refresh(db_vehicle)
    return db_vehicle


@router.get("", response_model=list[VehicleRead])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).all()


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return db_vehicle


@router.put("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(vehicle_id: int, vehicle: VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    db_vehicle.license_plate = vehicle.license_plate
    db_vehicle.vin = vehicle.vin
    db_vehicle.brand = vehicle.brand
    db_vehicle.model = vehicle.model
    db_vehicle.year = vehicle.year
    db_vehicle.fuel_type = vehicle.fuel_type
    db_vehicle.current_km = vehicle.current_km
    db_vehicle.note = vehicle.note

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Vehicle with this license plate or VIN already exists")

    db.refresh(db_vehicle)
    return db_vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    existing_assignment = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.vehicle_id == vehicle_id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=400,
            detail="Vehicle has assignments and cannot be deleted"
        )

    db.delete(db_vehicle)
    db.commit()

    return {"message": "Vehicle deleted successfully"}