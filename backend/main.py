from fastapi import FastAPI

from backend.db.database import Base, engine
from backend.models.vehicle import Vehicle
from backend.models.driver import Driver
from backend.models.assignment import DriverVehicleAssignment
from backend.routes.vehicles import router as vehicles_router
from backend.routes.drivers import router as drivers_router
from backend.routes.assignments import router as assignments_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CARLION API")


@app.get("/")
def root():
    return {"message": "CARLION backend bezi"}


app.include_router(vehicles_router)
app.include_router(drivers_router)
app.include_router(assignments_router)