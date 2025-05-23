# File: app/crud/event.py
from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import datetime
import json

from app.crud.base import CRUDBase
from app.models.event import Event, EventVersion
from app.models.permission import Permission, RoleType
from app.models.changelog import ChangeLog, ChangeType
from app.schemas.event import EventCreate, EventUpdate, EventFilterParams


class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: EventCreate, owner_id: int
    ) -> Event:
        obj_in_data = obj_in.dict()
        db_obj = Event(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.flush()  # Get the ID without committing

        # Create the initial version
        version = EventVersion(
            event_id=db_obj.id,
            version_number=1,
            title=db_obj.title,
            description=db_obj.description,
            start_time=db_obj.start_time,
            end_time=db_obj.end_time,
            location=db_obj.location,
            is_recurring=db_obj.is_recurring,
            recurrence_pattern=db_obj.recurrence_pattern,
            created_by_id=owner_id,
        )
        db.add(version)

        # Add owner permission
        permission = Permission(
            event_id=db_obj.id,
            user_id=owner_id,
            role=RoleType.OWNER,
        )
        db.add(permission)

        # Add to changelog
        changelog = ChangeLog(
            event_id=db_obj.id,
            user_id=owner_id,
            change_type=ChangeType.CREATE,
            to_version=1,
        )
        db.add(changelog)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_with_version(
        self,
        db: Session,
        *,
        db_obj: Event,
        obj_in: Union[EventUpdate, Dict[str, Any]],
        user_id: int
    ) -> Event:
        # Create a new version
        new_version_number = db_obj.current_version + 1
        
        # Get the changes for changelog
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        # Track the changes for the changelog
        changes = {}
        for field in update_data:
            old_value = getattr(db_obj, field)
            new_value = update_data[field]
            
            # Only track if the value actually changed
            if old_value != new_value:
                # For complex objects like recurrence_pattern
                if hasattr(old_value, "__dict__"):
                    old_value = old_value.__dict__
                if hasattr(new_value, "__dict__"):
                    new_value = new_value.__dict__
                    
                changes[field] = {
                    "old": old_value,
                    "new": new_value
                }
        
        # Create a new version entry
        version = EventVersion(
            event_id=db_obj.id,
            version_number=new_version_number,
            title=update_data.get("title", db_obj.title),
            description=update_data.get("description", db_obj.description),
            start_time=update_data.get("start_time", db_obj.start_time),
            end_time=update_data.get("end_time", db_obj.end_time),
            location=update_data.get("location", db_obj.location),
            is_recurring=update_data.get("is_recurring", db_obj.is_recurring),
            recurrence_pattern=update_data.get("recurrence_pattern", db_obj.recurrence_pattern),
            created_by_id=user_id,
        )
        db.add(version)
        
        # Update the event's current version
        update_data["current_version"] = new_version_number
        
        # Update the event
        updated_event = super().update(db, db_obj=db_obj, obj_in=update_data)
        
        # Add to changelog if there were actual changes
        if changes:
            changelog = ChangeLog(
                event_id=db_obj.id,
                user_id=user_id,
                change_type=ChangeType.UPDATE,
                from_version=db_obj.current_version,
                to_version=new_version_number,
                changes=changes,
            )
            db.add(changelog)
            db.commit()
            
        return updated_event

    def get_user_events(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        filter_params: Optional[EventFilterParams] = None
    ) -> List[Event]:
        # Base query: Get events where user has permissions
        query = (
            db.query(Event)
            .join(Permission, Event.id == Permission.event_id)
            .filter(Permission.user_id == user_id)
        )
        
        # Apply filters if provided
        if filter_params:
            if filter_params.start_date:
                query = query.filter(Event.end_time >= filter_params.start_date)
            if filter_params.end_date:
                query = query.filter(Event.start_time <= filter_params.end_date)
            if filter_params.title_search:
                query = query.filter(Event.title.ilike(f"%{filter_params.title_search}%"))
            if filter_params.location:
                query = query.filter(Event.location.ilike(f"%{filter_params.location}%"))
            if not filter_params.include_recurring:
                query = query.filter(Event.is_recurring == False)
                
        return query.offset(skip).limit(limit).all()
    
    def count_user_events(
        self, 
        db: Session, 
        user_id: int,
        filter_params: Optional[EventFilterParams] = None
    ) -> int:
        # Base query: Count events where user has permissions
        query = (
            db.query(func.count(Event.id))
            .join(Permission, Event.id == Permission.event_id)
            .filter(Permission.user_id == user_id)
        )
        
        # Apply filters if provided
        if filter_params:
            if filter_params.start_date:
                query = query.filter(Event.end_time >= filter_params.start_date)
            if filter_params.end_date:
                query = query.filter(Event.start_time <= filter_params.end_date)
            if filter_params.title_search:
                query = query.filter(Event.title.ilike(f"%{filter_params.title_search}%"))
            if filter_params.location:
                query = query.filter(Event.location.ilike(f"%{filter_params.location}%"))
            if not filter_params.include_recurring:
                query = query.filter(Event.is_recurring == False)
                
        return query.scalar()

    def get_version(self, db: Session, event_id: int, version_number: int) -> Optional[EventVersion]:
        return (
            db.query(EventVersion)
            .filter(
                EventVersion.event_id == event_id,
                EventVersion.version_number == version_number
            )
            .first()
        )
    
    def get_all_versions(self, db: Session, event_id: int) -> List[EventVersion]:
        return (
            db.query(EventVersion)
            .filter(EventVersion.event_id == event_id)
            .order_by(EventVersion.version_number)
            .all()
        )
        
    def rollback_to_version(
        self, 
        db: Session, 
        event_id: int, 
        version_id: int, 
        user_id: int,
        comment: Optional[str] = None
    ) -> Event:
        # Get the event and the version to roll back to
        event = self.get(db, id=event_id)
        version = self.get_version(db, event_id, version_id)
        
        if not event or not version:
            return None
            
        # Create a new version based on the old one
        new_version_number = event.current_version + 1
        
        # Track changes for changelog
        changes = {}
        for field in ['title', 'description', 'start_time', 'end_time', 'location', 'is_recurring', 'recurrence_pattern']:
            old_value = getattr(event, field)
            new_value = getattr(version, field)
            
            # Only track if the value actually changed
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value
                }
        
        # Create a new version entry that copies the rolled-back version
        new_version = EventVersion(
            event_id=event.id,
            version_number=new_version_number,
            title=version.title,
            description=version.description,
            start_time=version.start_time,
            end_time=version.end_time,
            location=version.location,
            is_recurring=version.is_recurring,
            recurrence_pattern=version.recurrence_pattern,
            created_by_id=user_id,
        )
        db.add(new_version)
        
        # Update the event with values from the version
        update_data = {
            "title": version.title,
            "description": version.description,
            "start_time": version.start_time,
            "end_time": version.end_time,
            "location": version.location,
            "is_recurring": version.is_recurring,
            "recurrence_pattern": version.recurrence_pattern,
            "current_version": new_version_number,
        }
        
        # Update the event
        for field, value in update_data.items():
            setattr(event, field, value)
        
        # Add rollback to changelog
        changelog = ChangeLog(
            event_id=event.id,
            user_id=user_id,
            change_type=ChangeType.ROLLBACK,
            from_version=event.current_version,
            to_version=new_version_number,
            changes=changes,
            comment=comment
        )
        db.add(changelog)
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event
        
    def check_for_conflicts(self, db: Session, user_id: int, start_time: datetime, end_time: datetime) -> List[Event]:
        """Check for conflicting events in the time range"""
        return (
            db.query(Event)
            .join(Permission, Event.id == Permission.event_id)
            .filter(
                Permission.user_id == user_id,
                or_(
                    and_(Event.start_time <= start_time, Event.end_time >= start_time),
                    and_(Event.start_time <= end_time, Event.end_time >= end_time),
                    and_(Event.start_time >= start_time, Event.end_time <= end_time),
                )
            )
            .all()
        )
        
    def create_batch(
        self, db: Session, *, obj_ins: List[EventCreate], owner_id: int
    ) -> List[Event]:
        """Create multiple events in a batch"""
        created_events = []
        
        # Use a transaction to ensure all or nothing
        for obj_in in obj_ins:
            event = self.create_with_owner(db, obj_in=obj_in, owner_id=owner_id)
            created_events.append(event)
            
        return created_events


event_crud = CRUDEvent(Event)