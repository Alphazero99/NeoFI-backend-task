
from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.permission import Permission, RoleType
from app.models.event import Event
from app.models.user import User
from app.models.changelog import ChangeLog, ChangeType
from app.schemas.permission import PermissionCreate, PermissionUpdate


class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    def get_event_permissions(self, db: Session, event_id: int) -> List[Permission]:
        return db.query(Permission).filter(Permission.event_id == event_id).all()
    
    def get_user_permission(self, db: Session, event_id: int, user_id: int) -> Optional[Permission]:
        return (
            db.query(Permission)
            .filter(
                Permission.event_id == event_id,
                Permission.user_id == user_id
            )
            .first()
        )
    
    def get_user_events(self, db: Session, user_id: int) -> List[Event]:
        return (
            db.query(Event)
            .join(Permission, Event.id == Permission.event_id)
            .filter(Permission.user_id == user_id)
            .all()
        )
    
    def create_with_event_user(
        self, db: Session, *, obj_in: PermissionCreate, created_by_id: int
    ) -> Permission:
        
        existing = self.get_user_permission(
            db, event_id=obj_in.event_id, user_id=obj_in.user_id
        )
        
        if existing:
          
            existing.role = obj_in.role
            db.add(existing)
            
            
            changelog = ChangeLog(
                event_id=obj_in.event_id,
                user_id=created_by_id,
                change_type=ChangeType.PERMISSION_CHANGE,
                changes={
                    "user_id": obj_in.user_id,
                    "old_role": existing.role.value,
                    "new_role": obj_in.role.value
                }
            )
            db.add(changelog)
            db.commit()
            db.refresh(existing)
            return existing
        else:
        
            db_obj = Permission(
                event_id=obj_in.event_id,
                user_id=obj_in.user_id,
                role=obj_in.role
            )
            db.add(db_obj)
            
     
            changelog = ChangeLog(
                event_id=obj_in.event_id,
                user_id=created_by_id,
                change_type=ChangeType.SHARE,
                changes={
                    "user_id": obj_in.user_id,
                    "role": obj_in.role.value
                }
            )
            db.add(changelog)
            db.commit()
            db.refresh(db_obj)
            return db_obj
    
    def update_user_permission(
        self,
        db: Session,
        *,
        event_id: int,
        user_id: int,
        obj_in: Union[PermissionUpdate, Dict[str, Any]],
        updated_by_id: int
    ) -> Permission:
       
        db_obj = self.get_user_permission(db, event_id=event_id, user_id=user_id)
        
        if not db_obj:
            return None
            
      
        old_role = db_obj.role
        
        
        db_obj = super().update(db, db_obj=db_obj, obj_in=obj_in)
        
      
        if old_role != db_obj.role:
            changelog = ChangeLog(
                event_id=event_id,
                user_id=updated_by_id,
                change_type=ChangeType.PERMISSION_CHANGE,
                changes={
                    "user_id": user_id,
                    "old_role": old_role.value,
                    "new_role": db_obj.role.value
                }
            )
            db.add(changelog)
            db.commit()
            
        return db_obj
    
    def remove_user_permission(
        self, db: Session, *, event_id: int, user_id: int, removed_by_id: int
    ) -> Permission:
     
        db_obj = self.get_user_permission(db, event_id=event_id, user_id=user_id)
        
        if not db_obj:
            return None
            
      
        old_role = db_obj.role
        
     
        db.delete(db_obj)
        
       
        changelog = ChangeLog(
            event_id=event_id,
            user_id=removed_by_id,
            change_type=ChangeType.PERMISSION_CHANGE,
            changes={
                "user_id": user_id,
                "old_role": old_role.value,
                "new_role": None
            }
        )
        db.add(changelog)
        db.commit()
        
        return db_obj
    
    def check_user_can_edit(self, db: Session, event_id: int, user_id: int) -> bool:
        """Check if user has edit permissions (OWNER or EDITOR)"""
        permission = self.get_user_permission(db, event_id=event_id, user_id=user_id)
        
        if not permission:
            return False
            
        return permission.role in [RoleType.OWNER, RoleType.EDITOR]
    
    def check_user_can_view(self, db: Session, event_id: int, user_id: int) -> bool:
        """Check if user has any viewing permissions"""
        permission = self.get_user_permission(db, event_id=event_id, user_id=user_id)
        return permission is not None
    
    def check_user_is_owner(self, db: Session, event_id: int, user_id: int) -> bool:
        """Check if user is the owner"""
        permission = self.get_user_permission(db, event_id=event_id, user_id=user_id)
        
        if not permission:
            return False
            
        return permission.role == RoleType.OWNER
    
    def get_event_users_with_permissions(self, db: Session, event_id: int) -> List[Dict]:
        """Get all users with their permissions for an event"""
        return (
            db.query(
                Permission.user_id,
                Permission.role,
                User.username,
                User.email
            )
            .join(User, Permission.user_id == User.id)
            .filter(Permission.event_id == event_id)
            .all()
        )


permission_crud = CRUDPermission(Permission)