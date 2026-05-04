from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth import hash_password, verify_password
from backend.db.database import SessionLocal
from backend.models.user import User
from backend.schemas.user import LoginRequest, RegisterRequest, SubscriptionUpdate, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

TRIAL_DAYS = 30


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _check_access(user: User) -> None:
    """Raises 403 if trial/subscription expired (admins are exempt)."""
    if user.is_admin:
        return
    today = date.today()
    trial_ok = user.trial_expires_at and user.trial_expires_at >= today
    sub_ok = user.subscription_expires_at and user.subscription_expires_at >= today
    if not trial_ok and not sub_ok:
        raise HTTPException(status_code=403, detail="EXPIRED")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nie si prihlásený")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Neplatná relácia")
    _check_access(user)
    return user


@router.post("/register", response_model=UserRead)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Heslo musí mať aspoň 6 znakov")
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Používateľ s týmto menom už existuje")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        is_admin=False,
        trial_expires_at=date.today() + timedelta(days=TRIAL_DAYS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Nesprávne meno alebo heslo")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Účet je deaktivovaný")
    request.session["user_id"] = user.id
    return {"ok": True, "username": user.username, "is_admin": user.is_admin}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# --- Admin endpoints ---

@router.post("/users", response_model=UserRead)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Len admin môže vytvárať používateľov")
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Používateľ s týmto menom už existuje")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        is_admin=body.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Len admin môže vidieť používateľov")
    return db.query(User).all()


class ActiveUpdate(BaseModel):
    is_active: bool


class PasswordUpdate(BaseModel):
    password: str


@router.patch("/users/{user_id}/active", response_model=UserRead)
def set_user_active(
    user_id: int,
    body: ActiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Len admin")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Používateľ nenájdený")
    if user.username == "admin" and not body.is_active:
        raise HTTPException(status_code=400, detail="Hlavný admin nemôže byť deaktivovaný")
    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/password", response_model=UserRead)
def change_password(
    user_id: int,
    body: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Len admin")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Heslo musí mať aspoň 6 znakov")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Používateľ nenájdený")
    user.hashed_password = hash_password(body.password)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/subscription", response_model=UserRead)
def update_subscription(
    user_id: int,
    body: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Len admin")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Používateľ nenájdený")
    if body.trial_expires_at is not None:
        user.trial_expires_at = body.trial_expires_at
    if body.subscription_expires_at is not None:
        user.subscription_expires_at = body.subscription_expires_at
    if body.subscription_amount is not None:
        user.subscription_amount = body.subscription_amount
    db.commit()
    db.refresh(user)
    return user
