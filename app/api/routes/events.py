# File: app/api/routes/events.py
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import math

from app.api.deps import get_db, get_current_active_user, get_event_owner, get_event_editor, get_event_viewer
from app.crud.event import event_crud
from app.models.user import User
from app.schemas.event import (
    Event, EventCreate, EventUpdate, BatchEventCreate, 
    EventFilterParams, EventListResponse
)

router = APIRouter()


@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(
    *,
    db: Session = Depends(get_db),
    event_in: EventCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new event with current user as owner.
    """
    # Check for conflicts if needed
    conflicts = event_crud.check_for_conflicts(
        db, user_id=current_user.id, 
        start_time=event_in.start_time, 
        end_time=event_in.end_time
    )
    
    # Create the event
    event = event_crud.create_with_owner(
        db=db, obj_in=event_in, owner_id=current_user.id
    )
    
    return event


@router.get("", response_model=EventListResponse)
def read_events(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    title_search: Optional[str] = None,
    location: Optional[str] = None,
    include_recurring: bool = True,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve events for current user with pagination and filtering.
    """
    from datetime import datetime
    
    # Create filter params
    filter_params = EventFilterParams(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        title_search=title_search,
        location=location,
        include_recurring=include_recurring
    )
    
    # Get total count for pagination
    total = event_crud.count_user_events(db, user_id=current_user.id, filter_params=filter_params)
    
    # Get events
    events = event_crud.get_user_events(
        db, user_id=current_user.id, 
        skip=skip, limit=limit,
        filter_params=filter_params
    )
    
    # Calculate pagination info
    page = skip // limit + 1 if limit > 0 else 1
    pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "items": events,
        "total": total,
        "page": page,
        "page_size": limit,
        "pages": pages
    }


@router.get("/{id}", response_model=Event)
def read_event(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_event_viewer)
) -> Any:
    """
    Get event by ID.
    """
    event = event_crud.get(db=db, id=id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{id}", response_model=Event)
def update_event(
    *,
    db: Session = Depends(get_db),
    id: int,
    event_in: EventUpdate,
    current_user: User = Depends(get_event_editor)
) -> Any:
    """
    Update an event.
    """
    event = event_crud.get(db=db, id=id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check for time conflicts if changing time
    if event_in.start_time or event_in.end_time:
        start_time = event_in.start_time or event.start_time
        end_time = event_in.end_time or event.end_time
        
        # Check if end time is after start time
        if end_time < start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
            )
        
        # Check for conflicts with other events
        conflicts = event_crud.check_for_conflicts(
            db, user_id=current_user.id, 
            start_time=start_time, 
            end_time=end_time
        )
        
        # Filter out current event from conflicts
        conflicts = [e for e in conflicts if e.id != id]
    
    # Update the event
    event = event_crud.update_with_version(
        db=db, db_obj=event, obj_in=event_in, user_id=current_user.id
    )
    
    return event


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_event_owner)
) -> None:  # Change return type to None
    """
    Delete an event.
    """
    event = event_crud.get(db=db, id=id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event_crud.remove(db=db, id=id)
    # Don't return anything for 204 responses


@router.post("/batch", response_model=List[Event], status_code=status.HTTP_201_CREATED)
def create_batch_events(
    *,
    db: Session = Depends(get_db),
    batch_in: BatchEventCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create multiple events in a batch.
    """
    # Check if there are events to create
    if not batch_in.events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No events provided"
        )
    
    # Create events
    events = event_crud.create_batch(
        db=db, obj_ins=batch_in.events, owner_id=current_user.id
    )
    
    return events