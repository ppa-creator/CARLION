from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.driver import Driver
from backend.models.trip import Trip
from backend.models.vehicle import Vehicle
from backend.schemas.trip import TripCreate, TripRead

router = APIRouter(prefix="/trips", tags=["trips"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_trip_payload(payload: TripCreate) -> None:
    if payload.start_km is not None and payload.end_km is not None and payload.end_km < payload.start_km:
        raise HTTPException(status_code=400, detail="end_km cannot be lower than start_km")


def _validate_trip_relations(db: Session, payload: TripCreate) -> None:
    driver = db.query(Driver).filter(Driver.id == payload.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")


@router.post("", response_model=TripRead)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    _validate_trip_payload(trip)
    _validate_trip_relations(db, trip)

    db_trip = Trip(
        driver_id=trip.driver_id,
        vehicle_id=trip.vehicle_id,
        trip_date=trip.trip_date,
        start_km=trip.start_km,
        end_km=trip.end_km,
        distance_km=trip.distance_km,
        route=trip.route,
        route_from=trip.route_from,
        route_to=trip.route_to,
        purpose=trip.purpose,
        note=trip.note,
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip


@router.get("", response_model=list[TripRead])
def list_trips(db: Session = Depends(get_db)):
    return db.query(Trip).all()


@router.get("/{trip_id}", response_model=TripRead)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    db_trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return db_trip


@router.put("/{trip_id}", response_model=TripRead)
def update_trip(trip_id: int, trip: TripCreate, db: Session = Depends(get_db)):
    db_trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    _validate_trip_payload(trip)
    _validate_trip_relations(db, trip)

    db_trip.driver_id = trip.driver_id
    db_trip.vehicle_id = trip.vehicle_id
    db_trip.trip_date = trip.trip_date
    db_trip.start_km = trip.start_km
    db_trip.end_km = trip.end_km
    db_trip.distance_km = trip.distance_km
    db_trip.route = trip.route
    db_trip.route_from = trip.route_from
    db_trip.route_to = trip.route_to
    db_trip.purpose = trip.purpose
    db_trip.note = trip.note

    db.commit()
    db.refresh(db_trip)
    return db_trip


@router.delete("/{trip_id}")
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    db_trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    db.delete(db_trip)
    db.commit()

    return {"message": "Trip deleted successfully"}
