# File: app/api/routes/auth.py
from datetime import timedelta
from typing import Any
from app.api.deps import get_db, get_current_active_user

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud.user import user_crud
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, Token, RefreshToken, UserLogin

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
) -> Any:
    """
    Register a new user.
    """
    # Check if user with same username exists
    user = user_crud.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
        
    # Check if user with same email exists
    user = user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    user = user_crud.create(db, obj_in=user_in)
    return user


@router.post("/login", response_model=Token)
def login_user(
    *,
    db: Session = Depends(get_db),
    form_data: UserLogin
) -> Any:
    """
    Authenticate a user.
    """
    user = user_crud.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    *,
    db: Session = Depends(get_db),
    refresh_token_in: RefreshToken
) -> Any:
    """
    Refresh an authentication token.
    """
    from jose import jwt, JWTError
    from app.schemas.user import TokenPayload
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            refresh_token_in.refresh_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        # Check token type
        if token_data.type != "refresh":
            raise credentials_exception
            
        # Check if token is expired
        from datetime import datetime
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise credentials_exception
            
        user_id = token_data.sub
        user = user_crud.get(db, id=int(user_id))
        
        if not user:
            raise credentials_exception
            
        # Check if user is active
        if not user_crud.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
            
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except (JWTError, ValidationError):
        raise credentials_exception


@router.post("/logout")
def logout_user(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout a user.
    
    Note: JWT tokens can't be invalidated server-side.
    Client should discard the tokens.
    """
    return {"message": "Successfully logged out"}