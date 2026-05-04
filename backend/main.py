import secrets
import os

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from backend.db.database import Base, engine
from backend.models.vehicle import Vehicle
from backend.models.driver import Driver
from backend.models.assignment import DriverVehicleAssignment
from backend.models.trip import Trip
from backend.models.refuel import Refuel
from backend.models.user import User
from backend.routes.vehicles import router as vehicles_router
from backend.routes.drivers import router as drivers_router
from backend.routes.assignments import router as assignments_router
from backend.routes.trips import router as trips_router
from backend.routes.refuels import router as refuels_router
from backend.routes.auth import router as auth_router, get_current_user
from backend.auth import hash_password

Base.metadata.create_all(bind=engine)

# Auto-seed admin account if not exists
def _seed_admin():
    from backend.db.database import SessionLocal
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin_pass = os.environ.get("ADMIN_PASSWORD", "carlion2026")
            db.add(User(username="admin", hashed_password=hash_password(admin_pass), is_admin=True, is_active=True))
            db.commit()
    finally:
        db.close()

ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI(title="CARLION API", root_path=ROOT_PATH)

app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "carlion-secret-change-in-prod-2026"), max_age=86400)

_seed_admin()

templates = Jinja2Templates(directory="backend/templates")


@app.get("/")
def root(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/ui")
    return RedirectResponse(url="/login")


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/ui")
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/ui")
    return templates.TemplateResponse(request=request, name="register.html", context={})




app.include_router(auth_router)

_auth_dep = Depends(get_current_user)
app.include_router(vehicles_router, dependencies=[_auth_dep])
app.include_router(drivers_router, dependencies=[_auth_dep])
app.include_router(assignments_router, dependencies=[_auth_dep])
app.include_router(trips_router, dependencies=[_auth_dep])
app.include_router(refuels_router, dependencies=[_auth_dep])