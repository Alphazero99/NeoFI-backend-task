# File: app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.base import SessionLocal
from app.core.config import settings
from app.core.security import oauth2_scheme
from app.models.permission import RoleType
from app.models.user import User
from app.schemas.user import TokenPayload


def get_db() -> Generator:
    """
    Dependency for database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current user from the token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.type != "access":
            raise credentials_exception
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise credentials_exception
        user_id: str = token_data.sub
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    from app.crud.user import user_crud
    user = user_crud.get(db, id=user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_current_user_with_permission(
    role: RoleType, event_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """
    Dependency for checking user has appropriate permission for an event
    """
    user_id = current_user.id
    
    from app.crud.permission import permission_crud
    
    if role == RoleType.OWNER:
        has_permission = permission_crud.check_user_is_owner(db, event_id=event_id, user_id=user_id)
    elif role == RoleType.EDITOR:
        has_permission = permission_crud.check_user_can_edit(db, event_id=event_id, user_id=user_id)
    else:  # VIEWER
        has_permission = permission_crud.check_user_can_view(db, event_id=event_id, user_id=user_id)
        
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User doesn't have {role.value} permission for this event"
        )
        
    return current_user


def get_event_owner(
    event_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """
    Dependency for checking user is the event owner
    """
    return get_current_user_with_permission(RoleType.OWNER, event_id, current_user, db)


def get_event_editor(
    event_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """
    Dependency for checking user can edit the event
    """
    return get_current_user_with_permission(RoleType.EDITOR, event_id, current_user, db)


def get_event_viewer(
    event_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """
    Dependency for checking user can view the event
    """
    return get_current_user_with_permission(RoleType.VIEWER, event_id, current_user, db)