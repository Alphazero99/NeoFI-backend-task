# File: app/utils/recurrence.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import dateutil.rrule as rrule


def parse_recurrence_pattern(pattern: Dict[str, Any]) -> rrule.rrule:
    """
    Parse a recurrence pattern dictionary into a dateutil.rrule
    """
    freq_map = {
        "daily": rrule.DAILY,
        "weekly": rrule.WEEKLY,
        "monthly": rrule.MONTHLY,
        "yearly": rrule.YEARLY
    }
    
    # Get frequency
    freq = freq_map.get(pattern.get("frequency", "daily").lower(), rrule.DAILY)
    
    # Build kwargs for rrule
    kwargs = {
        "freq": freq,
        "interval": pattern.get("interval", 1)
    }
    
    # Add count if present
    if "count" in pattern and pattern["count"] is not None:
        kwargs["count"] = pattern["count"]
    
    # Add until if present
    if "until" in pattern and pattern["until"] is not None:
        if isinstance(pattern["until"], str):
            # Parse ISO string to datetime
            kwargs["until"] = datetime.fromisoformat(pattern["until"])
        else:
            kwargs["until"] = pattern["until"]
    
    # Add byweekday if present
    if "weekdays" in pattern and pattern["weekdays"]:
        byweekday = []
        weekday_map = [
            rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU
        ]
        for day in pattern["weekdays"]:
            if 0 <= day <= 6:
                byweekday.append(weekday_map[day])
        if byweekday:
            kwargs["byweekday"] = byweekday
    
    # Add bymonthday if present
    if "monthdays" in pattern and pattern["monthdays"]:
        kwargs["bymonthday"] = pattern["monthdays"]
    
    # Add bymonth if present
    if "months" in pattern and pattern["months"]:
        kwargs["bymonth"] = pattern["months"]
    
    return rrule.rrule(**kwargs)


def get_recurrence_occurrences(
    start_time: datetime,
    pattern: Dict[str, Any],
    start_range: Optional[datetime] = None,
    end_range: Optional[datetime] = None,
    max_occurrences: int = 100
) -> List[datetime]:
    """
    Get a list of occurrences for a recurrence pattern within a date range
    """
    if not pattern:
        return [start_time]
    
    # Parse recurrence rule
    rule = parse_recurrence_pattern(pattern)
    
    # Set default range if not provided
    if not start_range:
        start_range = start_time
    if not end_range:
        end_range = start_time + timedelta(days=365)  # Default to one year
    
    # Get occurrences
    occurrences = list(rule.between(start_range, end_range, inc=True))
    
    # Limit number of occurrences
    return occurrences[:max_occurrences]


def format_recurrence_description(pattern: Dict[str, Any]) -> str:
    """
    Format a human-readable description of the recurrence pattern
    """
    if not pattern:
        return "One-time event"
    
    freq = pattern.get("frequency", "").lower()
    interval = pattern.get("interval", 1)
    
    if freq == "daily":
        base = f"Every day" if interval == 1 else f"Every {interval} days"
    elif freq == "weekly":
        base = f"Every week" if interval == 1 else f"Every {interval} weeks"
        
        # Add weekdays if specified
        weekdays = pattern.get("weekdays", [])
        if weekdays:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_str = ", ".join(day_names[day] for day in weekdays)
            base += f" on {days_str}"
    elif freq == "monthly":
        base = f"Every month" if interval == 1 else f"Every {interval} months"
        
        # Add monthdays if specified
        monthdays = pattern.get("monthdays", [])
        if monthdays:
            days_str = ", ".join(str(day) for day in monthdays)
            
            # Handle ordinals
            if len(monthdays) == 1:
                day = monthdays[0]
                if day == 1:
                    day_str = "1st"
                elif day == 2:
                    day_str = "2nd"
                elif day == 3:
                    day_str = "3rd"
                else:
                    day_str = f"{day}th"
                base += f" on the {day_str}"
            else:
                base += f" on days {days_str}"
    elif freq == "yearly":
        base = f"Every year" if interval == 1 else f"Every {interval} years"
        
        # Add months if specified
        months = pattern.get("months", [])
        if months:
            month_names = ["January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
            months_str = ", ".join(month_names[month-1] for month in months)
            base += f" in {months_str}"
    else:
        return "Custom recurrence"
    
    # Add 'until' or 'count' if specified
    if "until" in pattern and pattern["until"]:
        until_date = pattern["until"]
        if isinstance(until_date, str):
            until_date = datetime.fromisoformat(until_date)
        base += f" until {until_date.strftime('%Y-%m-%d')}"
    elif "count" in pattern and pattern["count"]:
        base += f" for {pattern['count']} occurrences"
    
    return base
