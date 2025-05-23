# File: app/api/routes/history.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_event_viewer, get_event_editor
from app.crud.event import event_crud
from app.models.user import User
from app.schemas.event import EventVersion
from app.schemas.changelog import RollbackRequest

router = APIRouter()


@router.get("/{id}/history/{version_id}", response_model=EventVersion)
def get_event_version(
    *,
    db: Session = Depends(get_db),
    id: int,
    version_id: int,
    current_user: User = Depends(get_event_viewer)
) -> Any:
    """
    Get a specific version of an event.
    """
    # Check if event exists
    event = event_crud.get(db, id=id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
        
    # Get the version
    version = event_crud.get_version(db, event_id=id, version_number=version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found"
        )
        
    return version


@router.post("/{id}/rollback/{version_id}", response_model=EventVersion)
def rollback_to_version(
    *,
    db: Session = Depends(get_db),
    id: int,
    version_id: int,
    rollback_in: RollbackRequest = None,
    current_user: User = Depends(get_event_editor)
) -> Any:
    """
    Rollback to a previous version.
    """
    # Check if event exists
    event = event_crud.get(db, id=id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
        
    # Check if version exists
    version = event_crud.get_version(db, event_id=id, version_number=version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found"
        )
        
    # Cannot rollback to current version
    if version_id == event.current_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rollback to current version"
        )
        
    # Perform rollback
    comment = None
    if rollback_in:
        comment = rollback_in.comment
        
    updated_event = event_crud.rollback_to_version(
        db, 
        event_id=id, 
        version_id=version_id, 
        user_id=current_user.id,
        comment=comment
    )
    
    # Get the new version
    new_version = event_crud.get_version(
        db, 
        event_id=id, 
        version_number=updated_event.current_version
    )
    
    return new_version