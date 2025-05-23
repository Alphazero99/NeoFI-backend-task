
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.base import CRUDBase
from app.models.changelog import ChangeLog, ChangeType
from app.models.event import EventVersion
from app.schemas.changelog import ChangeLogBase


class CRUDChangeLog(CRUDBase[ChangeLog, ChangeLogBase, ChangeLogBase]):
    def get_event_changelog(self, db: Session, event_id: int) -> List[ChangeLog]:
        """Get all changelog entries for an event, ordered by timestamp (newest first)"""
        return (
            db.query(ChangeLog)
            .filter(ChangeLog.event_id == event_id)
            .order_by(desc(ChangeLog.timestamp))
            .all()
        )
    
    def get_diff_between_versions(
        self, db: Session, event_id: int, version1: int, version2: int
    ) -> Dict[str, Any]:
        """Generate a diff between two versions of an event"""
     
        v1 = (
            db.query(EventVersion)
            .filter(
                EventVersion.event_id == event_id,
                EventVersion.version_number == version1
            )
            .first()
        )
        
        v2 = (
            db.query(EventVersion)
            .filter(
                EventVersion.event_id == event_id,
                EventVersion.version_number == version2
            )
            .first()
        )
        
        if not v1 or not v2:
            return None
            
       
        fields = ["title", "description", "start_time", "end_time", "location", "is_recurring", "recurrence_pattern"]
   
        diff = []
        for field in fields:
            old_value = getattr(v1, field)
            new_value = getattr(v2, field)
            
            
            if old_value != new_value:
                diff.append({
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value
                })
                
        return {
            "event_id": event_id,
            "version1": version1,
            "version2": version2,
            "changes": diff
        }
    
    def create_event_changelog(
        self, 
        db: Session, 
        event_id: int, 
        user_id: int, 
        change_type: ChangeType,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None
    ) -> ChangeLog:
        """Create a new changelog entry"""
        changelog = ChangeLog(
            event_id=event_id,
            user_id=user_id,
            change_type=change_type,
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            comment=comment
        )
        
        db.add(changelog)
        db.commit()
        db.refresh(changelog)
        return changelog


changelog_crud = CRUDChangeLog(ChangeLog)