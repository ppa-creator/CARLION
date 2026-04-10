from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
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
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.get("", response_model=list[VehicleRead])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).all()