from datetime import date, datetime, timedelta
import hashlib
import json
import logging
import os
import secrets
import socket
import smtplib
from email.message import EmailMessage
from urllib import error, request
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.auth import hash_password, verify_password
from backend.db.database import SessionLocal
from backend.models.email_verification import EmailVerification
from backend.models.user import User
from backend.models.user_email import UserEmail
from backend.schemas.user import LoginRequest, RegisterRequest, SubscriptionUpdate, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

TRIAL_DAYS = 30
VERIFY_TOKEN_HOURS = 24


class RegisterResponse(BaseModel):
    ok: bool
    email: EmailStr
    detail: str


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _env_nonempty(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _send_verification_via_resend(
    recipient_email: str,
    username: str,
    verify_link: str,
    resend_api_key: str,
    resend_from: str,
) -> None:
    payload = {
        "from": resend_from,
        "to": [recipient_email],
        "subject": "CARLION - overenie emailu",
        "text": (
            f"Ahoj {username},\n\n"
            f"klikni na tento odkaz pre overenie emailu a aktivaciu uctu:\n{verify_link}\n\n"
            f"Platnost odkazu je {VERIFY_TOKEN_HOURS} hodin.\n"
        ),
    }
    req = request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            if resp.status < 200 or resp.status >= 300:
                raise HTTPException(status_code=503, detail="Resend API vrátil neúspešnú odpoveď.")
    except error.HTTPError as ex:
        logger.warning("Resend HTTP error: %s", ex)
        raise HTTPException(
            status_code=503,
            detail="Email služba (Resend) odmietla odoslanie. Skontroluj RESEND_API_KEY a RESEND_FROM.",
        )
    except (error.URLError, TimeoutError, OSError) as ex:
        logger.warning("Resend connection failed: %s", ex)
        raise HTTPException(
            status_code=503,
            detail="Nepodarilo sa spojiť s email službou Resend.",
        )


def _send_verification_email(recipient_email: str, username: str, verify_token: str) -> None:
    app_base_url = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    verify_link = f"{app_base_url}/auth/verify-email?token={quote_plus(verify_token)}"

    resend_api_key = _env_nonempty("RESEND_API_KEY")
    resend_from = _env_nonempty("RESEND_FROM")
    if resend_api_key:
        if not resend_from:
            raise HTTPException(status_code=503, detail="Chýba RESEND_FROM pre Resend odosielanie.")
        _send_verification_via_resend(
            recipient_email=recipient_email,
            username=username,
            verify_link=verify_link,
            resend_api_key=resend_api_key,
            resend_from=resend_from,
        )
        return

    smtp_host = _env_nonempty("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = _env_nonempty("SMTP_USER")
    smtp_password = _env_nonempty("SMTP_PASSWORD")
    smtp_sender = _env_nonempty("SMTP_SENDER") or smtp_user

    missing = []
    if not smtp_host:
        missing.append("SMTP_HOST")
    if not smtp_sender:
        missing.append("SMTP_SENDER alebo SMTP_USER")

    if missing:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Email služba nie je nastavená (chýba: {', '.join(missing)}). "
                "Na Railway Free/Trial/Hobby použi RESEND_API_KEY + RESEND_FROM."
            ),
        )

    msg = EmailMessage()
    msg["Subject"] = "CARLION - overenie emailu"
    msg["From"] = smtp_sender
    msg["To"] = recipient_email
    msg.set_content(
        f"Ahoj {username},\n\n"
        f"klikni na tento odkaz pre overenie emailu a aktivaciu uctu:\n{verify_link}\n\n"
        f"Platnost odkazu je {VERIFY_TOKEN_HOURS} hodin.\n"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as ex:
        logger.warning("SMTP auth failed for sender %s: %s", smtp_sender, ex)
        raise HTTPException(
            status_code=503,
            detail="SMTP prihlásenie zlyhalo. Skontroluj SMTP_USER a SMTP_PASSWORD (pri Gmail použi App Password).",
        )
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, OSError, TimeoutError, socket.timeout) as ex:
        logger.warning("SMTP connection failed to %s:%s: %s", smtp_host, smtp_port, ex)
        raise HTTPException(
            status_code=503,
            detail=(
                "Nepodarilo sa spojiť so SMTP serverom. "
                "Na Railway Free/Trial/Hobby je SMTP blokované, použi Resend API (RESEND_API_KEY, RESEND_FROM)."
            ),
        )
    except smtplib.SMTPException as ex:
        logger.warning("SMTP send failed: %s", ex)
        raise HTTPException(
            status_code=503,
            detail="SMTP server odmietol odoslanie emailu. Skontroluj SMTP nastavenia odosielateľa.",
        )


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


@router.post("/register", response_model=RegisterResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Heslo musí mať aspoň 6 znakov")

    username = body.username.strip()
    email = body.email.strip().lower()

    if not username:
        raise HTTPException(status_code=400, detail="Používateľské meno je povinné")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Používateľ s týmto menom už existuje")

    existing_email = db.query(UserEmail).filter(UserEmail.email == email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Tento email je už použitý")

    # Clear expired pending records for same username/email.
    now = datetime.utcnow()
    db.query(EmailVerification).filter(
        EmailVerification.expires_at < now,
        (EmailVerification.username == username) | (EmailVerification.email == email),
    ).delete(synchronize_session=False)

    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)

    pending = db.query(EmailVerification).filter(
        (EmailVerification.username == username) | (EmailVerification.email == email)
    ).first()

    if pending:
        pending.username = username
        pending.email = email
        pending.hashed_password = hash_password(body.password)
        pending.token_hash = token_hash
        pending.expires_at = now + timedelta(hours=VERIFY_TOKEN_HOURS)
    else:
        db.add(
            EmailVerification(
                username=username,
                email=email,
                hashed_password=hash_password(body.password),
                token_hash=token_hash,
                expires_at=now + timedelta(hours=VERIFY_TOKEN_HOURS),
            )
        )

    db.commit()

    _send_verification_email(email, username, token)

    return {
        "ok": True,
        "email": email,
        "detail": "Na email bol odoslaný overovací odkaz.",
    }


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    token_hash = _hash_token(token)
    pending = db.query(EmailVerification).filter(EmailVerification.token_hash == token_hash).first()
    now = datetime.utcnow()

    if not pending or pending.expires_at < now:
        return RedirectResponse(url="/register?verify_error=invalid_or_expired")

    existing = db.query(User).filter(User.username == pending.username).first()
    if existing:
        db.delete(pending)
        db.commit()
        return RedirectResponse(url="/login?verified=1")

    used_email = db.query(UserEmail).filter(UserEmail.email == pending.email).first()
    if used_email:
        db.delete(pending)
        db.commit()
        return RedirectResponse(url="/register?verify_error=email_used")

    user = User(
        username=pending.username,
        hashed_password=pending.hashed_password,
        is_admin=False,
        is_active=True,
        trial_expires_at=date.today() + timedelta(days=TRIAL_DAYS),
    )
    db.add(user)
    db.flush()

    db.add(UserEmail(user_id=user.id, email=pending.email))
    db.delete(pending)
    db.commit()

    return RedirectResponse(url="/login?verified=1")


@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Nesprávne meno alebo heslo")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Účet je neaktívny alebo neoverený")
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
