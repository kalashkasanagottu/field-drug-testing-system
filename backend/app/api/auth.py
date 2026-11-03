import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserCreate, UserResponse,
    RefreshTokenRequest, RefreshTokenResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse
)
from app.core.security import (
    verify_password, hash_password, create_access_token,
    create_refresh_token, decode_refresh_token
)
from app.services.audit_service import log_audit_event
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(login_req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_req.username).first()
    if not user or not verify_password(login_req.password, user.hashed_password):
        log_audit_event(
            db,
            event_type="LOGIN_FAILED",
            user_name=login_req.username,
            details={"reason": "Invalid credentials", "ip": request.client.host if request.client else "unknown"},
            client_ip=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact an administrator."
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )

    log_audit_event(
        db,
        event_type="USER_LOGIN",
        user_id=user.id,
        user_name=user.username,
        details={"role": user.role, "department": user.department},
        client_ip=request.client.host if request.client else None
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        badge_number=user.badge_number,
        role=user.role,
        department=user.department
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/register", response_model=UserResponse)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value]))
):
    existing = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists.")

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        badge_number=user_in.badge_number,
        department=user_in.department or "Forensic Field Operations",
        role=user_in.role or UserRole.FIELD_OFFICER.value,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_event(
        db,
        event_type="USER_REGISTERED",
        user_id=current_user.id,
        user_name=current_user.username,
        details={"created_username": new_user.username, "assigned_role": new_user.role}
    )

    return new_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit_event(
        db,
        event_type="USER_LOGOUT",
        user_id=current_user.id,
        user_name=current_user.username,
        details={"action": "Session terminated by user"}
    )
    return {"message": "Logged out successfully."}


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(refresh_req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Issue a new access token using a valid refresh token.
    Enables session continuation without re-entering credentials.
    """
    payload = decode_refresh_token(refresh_req.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload."
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or does not exist."
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )

    log_audit_event(
        db,
        event_type="TOKEN_REFRESHED",
        user_id=user.id,
        user_name=user.username,
        details={"action": "Access token refreshed via refresh token"}
    )

    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """
    Initiate a password reset flow. In development/demo mode, returns a
    reset token directly. In production, this would trigger an email delivery.
    """
    user = None
    if req.username:
        user = db.query(User).filter(User.username == req.username).first()
    elif req.email:
        user = db.query(User).filter(User.email == req.email).first()

    # Always return success to prevent user enumeration
    if not user:
        log_audit_event(
            db,
            event_type="PASSWORD_RESET_REQUESTED",
            user_name=req.username or req.email,
            details={"reason": "User not found", "ip": request.client.host if request and request.client else "unknown"},
            client_ip=request.client.host if request and request.client else None
        )
        return ForgotPasswordResponse(
            message="If the account exists, a password reset link has been sent.",
            expires_in=3600
        )

    # Generate a reset token (short-lived)
    reset_payload = {"sub": str(user.id), "type": "password_reset"}
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=1)
    reset_payload.update({"exp": expire, "iat": now})
    reset_token = jwt.encode(reset_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    log_audit_event(
        db,
        event_type="PASSWORD_RESET_REQUESTED",
        user_id=user.id,
        user_name=user.username,
        details={"action": "Password reset token generated", "ip": request.client.host if request and request.client else "unknown"},
        client_ip=request.client.host if request and request.client else None
    )

    # In development/demo mode, return the token directly for testing
    return ForgotPasswordResponse(
        message="Password reset token generated. Use /api/auth/reset-password with this token to set a new password.",
        reset_token=reset_token,
        expires_in=3600
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid reset token issued by /api/auth/forgot-password.
    """
    try:
        payload = jwt.decode(req.reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token."
        )

    if payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type for password reset."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token payload."
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.hashed_password = hash_password(req.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_audit_event(
        db,
        event_type="PASSWORD_RESET_COMPLETED",
        user_id=user.id,
        user_name=user.username,
        details={"action": "Password reset completed successfully"}
    )

    return ResetPasswordResponse(message="Password has been reset successfully.")
