from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.db.database import SessionLocal
from backend.models.driver import Driver
from backend.models.refuel import Refuel
from backend.models.trip import Trip
from backend.models.vehicle import Vehicle
from backend.schemas.refuel import RefuelCreate, RefuelRead

router = APIRouter(prefix="/refuels", tags=["refuels"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_refuel_payload(payload: RefuelCreate) -> None:
    if payload.liters <= 0:
        raise HTTPException(status_code=400, detail="liters must be greater than 0")

    if payload.total_cost <= 0:
        raise HTTPException(status_code=400, detail="total_cost must be greater than 0")

    if payload.price_per_liter is not None and payload.price_per_liter <= 0:
        raise HTTPException(status_code=400, detail="price_per_liter must be greater than 0")


def _validate_refuel_relations(db: Session, payload: RefuelCreate) -> None:
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if payload.driver_id is not None:
        driver = db.query(Driver).filter(Driver.id == payload.driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")


@router.post("", response_model=RefuelRead)
def create_refuel(refuel: RefuelCreate, db: Session = Depends(get_db)):
    _validate_refuel_payload(refuel)
    _validate_refuel_relations(db, refuel)

    db_refuel = Refuel(
        vehicle_id=refuel.vehicle_id,
        driver_id=refuel.driver_id,
        refuel_date=refuel.refuel_date,
        refuel_time=refuel.refuel_time,
        liters=refuel.liters,
        total_cost=refuel.total_cost,
        price_per_liter=refuel.price_per_liter,
        odometer_km=refuel.odometer_km,
        station=refuel.station,
        fuel_type=refuel.fuel_type,
        note=refuel.note,
        trip_id=refuel.trip_id,
    )
    db.add(db_refuel)
    db.commit()
    db.refresh(db_refuel)
    return db_refuel


@router.get("", response_model=list[RefuelRead])
def list_refuels(db: Session = Depends(get_db)):
    return db.query(Refuel).all()


@router.get("/{refuel_id}", response_model=RefuelRead)
def get_refuel(refuel_id: int, db: Session = Depends(get_db)):
    db_refuel = db.query(Refuel).filter(Refuel.id == refuel_id).first()

    if not db_refuel:
        raise HTTPException(status_code=404, detail="Refuel not found")

    return db_refuel


@router.put("/{refuel_id}", response_model=RefuelRead)
def update_refuel(refuel_id: int, refuel: RefuelCreate, db: Session = Depends(get_db)):
    db_refuel = db.query(Refuel).filter(Refuel.id == refuel_id).first()

    if not db_refuel:
        raise HTTPException(status_code=404, detail="Refuel not found")

    _validate_refuel_payload(refuel)
    _validate_refuel_relations(db, refuel)

    db_refuel.vehicle_id = refuel.vehicle_id
    db_refuel.driver_id = refuel.driver_id
    db_refuel.refuel_date = refuel.refuel_date
    db_refuel.refuel_time = refuel.refuel_time
    db_refuel.liters = refuel.liters
    db_refuel.total_cost = refuel.total_cost
    db_refuel.price_per_liter = refuel.price_per_liter
    db_refuel.odometer_km = refuel.odometer_km
    db_refuel.station = refuel.station
    db_refuel.fuel_type = refuel.fuel_type
    db_refuel.note = refuel.note
    db_refuel.trip_id = refuel.trip_id

    db.commit()
    db.refresh(db_refuel)
    return db_refuel


@router.delete("/{refuel_id}")
def delete_refuel(refuel_id: int, db: Session = Depends(get_db)):
    db_refuel = db.query(Refuel).filter(Refuel.id == refuel_id).first()

    if not db_refuel:
        raise HTTPException(status_code=404, detail="Refuel not found")

    db.delete(db_refuel)
    db.commit()

    return {"message": "Refuel deleted successfully"}


@router.patch("/{refuel_id}/assign-trip", response_model=RefuelRead)
def assign_trip(refuel_id: int, trip_id: Optional[int] = None, db: Session = Depends(get_db)):
    db_refuel = db.query(Refuel).filter(Refuel.id == refuel_id).first()
    if not db_refuel:
        raise HTTPException(status_code=404, detail="Refuel not found")

    if trip_id is not None:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

    db_refuel.trip_id = trip_id
    db.commit()
    db.refresh(db_refuel)
    return db_refuel


@router.get("/by-date/{date}", response_model=list[RefuelRead])
def refuels_by_date(date: str, db: Session = Depends(get_db)):
    from datetime import date as date_type
    try:
        parsed = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")
    return db.query(Refuel).filter(Refuel.refuel_date == parsed).all()
