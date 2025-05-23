
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def serialize_value(value: Any) -> Any:
    """
    Serialize complex values for comparison and storage
    """
    if value is None:
        return None
    
    if isinstance(value, (str, int, float, bool)):
        return value
    
    if isinstance(value, datetime):
        return value.isoformat()
    
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    
    
    if hasattr(value, "__dict__"):
        return serialize_value(value.__dict__)
    
    
    return str(value)


def generate_field_diff(old_value: Any, new_value: Any) -> Dict[str, Any]:
    """
    Generate a diff for a single field
    """
   
    old_serialized = serialize_value(old_value)
    new_serialized = serialize_value(new_value)
    

    return {
        "old": old_serialized,
        "new": new_serialized
    }


def generate_object_diff(old_obj: Dict[str, Any], new_obj: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Generate a diff between two object dictionaries
    """
    diff = {}
    
  
    all_keys = set(old_obj.keys()) | set(new_obj.keys())
    
    for key in all_keys:
        old_value = old_obj.get(key)
        new_value = new_obj.get(key)
        
       
        if old_value == new_value:
            continue
        
  
        diff[key] = generate_field_diff(old_value, new_value)
    
    return diff


def format_diff_for_display(diff: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format the diff for display
    """
    formatted = []
    
    for field, change in diff.items():
        formatted.append({
            "field": field,
            "old_value": change.get("old"),
            "new_value": change.get("new")
        })
    
    return formatted