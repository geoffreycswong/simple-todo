import uuid
from sqlalchemy.orm import Session
from . import models, crud
from .database import SessionLocal
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(crud.VersionMismatchError),
    reraise=True
)
def _update_single_dependent(db: Session, dependent_id: uuid.UUID):
    # Re-fetch latest version to ensure we have the most current data
    dependent = db.query(models.Todo).filter(models.Todo.id == dependent_id).first()
    if not dependent:
        return

    current_version = dependent.version
    # A task is blocked if any of its prerequisites are not Completed
    new_is_blocked = any(p.status != "Completed" for p in dependent.prerequisites)
    
    if dependent.is_blocked != new_is_blocked:
        # Atomic update with version check for OCC
        rows_affected = db.query(models.Todo).filter(
            models.Todo.id == dependent_id,
            models.Todo.version == current_version
        ).update({
            "is_blocked": new_is_blocked,
            "version": models.Todo.version + 1
        }, synchronize_session=False)
        
        if rows_affected == 0:
            # This means someone else updated the task between our fetch and update
            raise crud.VersionMismatchError(f"Version mismatch for task {dependent_id} during propagation")
        
        db.commit()

def propagate_dependency_status(task_id: uuid.UUID):
    """
    Background task to propagate blocked status to all tasks depending on task_id.
    """
    db = SessionLocal()
    try:
        # Find the task that was just updated
        task = db.query(models.Todo).filter(models.Todo.id == task_id).first()
        if not task:
            return
        
        # Propagate to all direct dependents
        for dependent in task.dependents:
            _update_single_dependent(db, dependent.id)
    finally:
        db.close()
