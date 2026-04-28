from datetime import datetime
from dateutil.rrule import rrulestr
from typing import Optional

def calculate_next_due_date(
    recurrence_rule: str,
    current_due_date: Optional[datetime],
    anchor: str = "DUE_DATE",
    completion_date: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Calculates the next due date for a recurring task based on its recurrence rule and anchor.
    """
    if not recurrence_rule:
        return None
    
    # The anchor determines from which date we calculate the next occurrence
    if anchor == "COMPLETION_DATE":
        # Start calculating from the time of completion
        base_date = completion_date or datetime.now()
    else: # Default to DUE_DATE
        # Start calculating from the original due date
        base_date = current_due_date or datetime.now()
        
    try:
        rule = rrulestr(recurrence_rule, dtstart=base_date)
        # rule.after(base_date) returns the first occurrence strictly after the base_date
        next_date = rule.after(base_date)
        return next_date
    except Exception:
        # If the rule is invalid, return None
        return None
