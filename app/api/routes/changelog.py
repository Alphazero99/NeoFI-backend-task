
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_event_viewer
from app.crud.changelog import changelog_crud
from app.crud.event import event_crud
from app.models.user import User
from app.schemas.changelog import ChangeLogList, DiffResponse

router = APIRouter()


@router.get("/{id}/changelog", response_model=ChangeLogList)
def get_event_changelog(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_event_viewer)
) -> Any:
    """
    Get a chronological log of all changes to an event.
    """
   
    event = event_crud.get(db, id=id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
        
    
    changes = changelog_crud.get_event_changelog(db, event_id=id)
    
    return {
        "event_id": id,
        "changes": changes
    }


@router.get("/{id}/diff/{version_id1}/{version_id2}", response_model=DiffResponse)
def get_version_diff(
    *,
    db: Session = Depends(get_db),
    id: int,
    version_id1: int,
    version_id2: int,
    current_user: User = Depends(get_event_viewer)
) -> Any:
    """
    Get a diff between two versions.
    """
  
    event = event_crud.get(db, id=id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
        
   
    v1 = event_crud.get_version(db, event_id=id, version_number=version_id1)
    if not v1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id1} not found"
        )
        
    v2 = event_crud.get_version(db, event_id=id, version_number=version_id2)
    if not v2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id2} not found"
        )
        
    diff = changelog_crud.get_diff_between_versions(
        db, 
        event_id=id, 
        version1=version_id1, 
        version2=version_id2
    )
    
    return diff