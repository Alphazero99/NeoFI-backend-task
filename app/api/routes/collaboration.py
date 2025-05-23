
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_event_owner, get_event_editor
from app.crud.permission import permission_crud
from app.crud.user import user_crud
from app.models.user import User
from app.schemas.permission import (
    Permission, PermissionCreate, PermissionUpdate, 
    ShareEventRequest, EventPermissionsList, UserPermissionInfo
)

router = APIRouter()


@router.post("/{id}/share", response_model=List[Permission])
def share_event(
    *,
    db: Session = Depends(get_db),
    id: int,
    share_in: ShareEventRequest,
    current_user: User = Depends(get_event_owner)
) -> Any:
    """
    Share an event with other users.
    """
    created_permissions = []
    
    for permission_in in share_in.users:
        
        user = user_crud.get(db, id=permission_in.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {permission_in.user_id} not found"
            )
            
      
        event = db.query(permission_crud.model).filter_by(event_id=id, user_id=current_user.id).first()
        if event and permission_in.user_id == current_user.id:
            continue
            
    
        permission = permission_crud.create_with_event_user(
            db=db, 
            obj_in=PermissionCreate(
                event_id=id,
                user_id=permission_in.user_id,
                role=permission_in.role
            ),
            created_by_id=current_user.id
        )
        
        created_permissions.append(permission)
    
    return created_permissions


@router.get("/{id}/permissions", response_model=EventPermissionsList)
def get_event_permissions(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_event_editor)
) -> Any:
    """
    List all permissions for an event.
    """
   
    users_with_permissions = permission_crud.get_event_users_with_permissions(db, event_id=id)
    
 
    permissions = []
    for user_id, role, username, email in users_with_permissions:
        permissions.append(
            UserPermissionInfo(
                user_id=user_id,
                username=username,
                email=email,
                role=role
            )
        )
    
    return {
        "event_id": id,
        "permissions": permissions
    }


@router.put("/{id}/permissions/{user_id}", response_model=Permission)
def update_permission(
    *,
    db: Session = Depends(get_db),
    id: int,
    user_id: int,
    permission_in: PermissionUpdate,
    current_user: User = Depends(get_event_owner)
) -> Any:
    """
    Update permissions for a user.
    """

    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if permission_crud.check_user_is_owner(db, event_id=id, user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner's permission"
        )

    permission = permission_crud.update_user_permission(
        db=db,
        event_id=id,
        user_id=user_id,
        obj_in=permission_in,
        updated_by_id=current_user.id
    )
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
        
    return permission


@router.delete("/{id}/permissions/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_permission(
    *,
    db: Session = Depends(get_db),
    id: int,
    user_id: int,
    current_user: User = Depends(get_event_owner)
) -> None:  
    """
    Remove access for a user.
    """
    
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    
    if permission_crud.check_user_is_owner(db, event_id=id, user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove owner's permission"
        )
        
 
    permission = permission_crud.remove_user_permission(
        db=db,
        event_id=id,
        user_id=user_id,
        removed_by_id=current_user.id
    )
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    