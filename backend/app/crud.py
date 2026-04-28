import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models, schemas
from .recurrence import calculate_next_due_date

class VersionMismatchError(Exception):
    pass

def get_todo(db: Session, todo_id: uuid.UUID):
    return db.query(models.Todo).filter(models.Todo.id == todo_id, models.Todo.deleted_at == None).first()

def get_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    due_date_before: Optional[datetime] = None,
    due_date_after: Optional[datetime] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    is_deleted: bool = False
):
    if is_deleted:
        query = db.query(models.Todo).filter(models.Todo.deleted_at != None)
    else:
        query = db.query(models.Todo).filter(models.Todo.deleted_at == None)
    
    # Mandatory Filter: exclude "Archived" unless explicitly requested
    if status:
        query = query.filter(models.Todo.status == status)
    else:
        query = query.filter(models.Todo.status != "Archived")
    
    if priority:
        query = query.filter(models.Todo.priority == priority)
    
    if is_blocked is not None:
        query = query.filter(models.Todo.is_blocked == is_blocked)
        
    if due_date_before:
        query = query.filter(models.Todo.due_date <= due_date_before)
        
    if due_date_after:
        query = query.filter(models.Todo.due_date >= due_date_after)
        
    # Sorting logic
    if sort_by:
        column = None
        if sort_by == "due_date":
            column = models.Todo.due_date
        elif sort_by == "priority":
            column = models.Todo.priority
        elif sort_by == "status":
            column = models.Todo.status
        elif sort_by == "name":
            column = models.Todo.title
            
        if column is not None:
            if order == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
    
    return query.offset(skip).limit(limit).all()

def count_todos(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    due_date_before: Optional[datetime] = None,
    due_date_after: Optional[datetime] = None,
    is_deleted: bool = False
) -> int:
    if is_deleted:
        query = db.query(models.Todo).filter(models.Todo.deleted_at != None)
    else:
        query = db.query(models.Todo).filter(models.Todo.deleted_at == None)
        
    if status:
        query = query.filter(models.Todo.status == status)
    else:
        query = query.filter(models.Todo.status != "Archived")
    if priority:
        query = query.filter(models.Todo.priority == priority)
    if is_blocked is not None:
        query = query.filter(models.Todo.is_blocked == is_blocked)
    if due_date_before:
        query = query.filter(models.Todo.due_date <= due_date_before)
    if due_date_after:
        query = query.filter(models.Todo.due_date >= due_date_after)
    return query.count()

def create_todo(db: Session, todo: schemas.TodoCreate):
    todo_data = todo.model_dump(exclude={"dependency_ids"})
    db_todo = models.Todo(**todo_data)
    
    if todo.dependency_ids:
        from fastapi import HTTPException
        prerequisites = db.query(models.Todo).filter(
            models.Todo.id.in_(todo.dependency_ids),
            models.Todo.deleted_at == None
        ).all()
        if len(prerequisites) != len(todo.dependency_ids):
            raise HTTPException(status_code=400, detail="One or more dependencies do not exist or are deleted")
        db_todo.prerequisites = prerequisites
        # Calculate is_blocked: True if any prerequisite is not "Completed"
        db_todo.is_blocked = any(p.status != "Completed" for p in prerequisites)
    
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def handle_recurrence(db: Session, db_todo: models.Todo):
    if db_todo.recurrence_rule and db_todo.status == "Completed":
        next_due_date = calculate_next_due_date(
            db_todo.recurrence_rule,
            db_todo.due_date,
            db_todo.recurrence_anchor,
            datetime.utcnow()
        )
        
        if next_due_date:
            new_todo = models.Todo(
                title=db_todo.title,
                description=db_todo.description,
                priority=db_todo.priority,
                due_date=next_due_date,
                recurrence_rule=db_todo.recurrence_rule,
                recurrence_anchor=db_todo.recurrence_anchor,
                status="Not Started",
                version=1,
                prerequisites=db_todo.prerequisites,
                is_blocked=any(p.status != "Completed" for p in db_todo.prerequisites)
            )
            db.add(new_todo)
            return new_todo
    return None

def update_todo(db: Session, todo_id: uuid.UUID, todo: schemas.TodoUpdate):
    db_todo = get_todo(db, todo_id)
    if not db_todo:
        return None
    
    if db_todo.version != todo.version:
        raise VersionMismatchError("Task version mismatch")

    old_status = db_todo.status
    update_data = todo.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key not in ["version", "dependency_ids"]:
            setattr(db_todo, key, value)
    
    # Handle dependencies separately
    if "dependency_ids" in update_data:
        if update_data["dependency_ids"] is not None:
            from fastapi import HTTPException
            prerequisites = db.query(models.Todo).filter(
                models.Todo.id.in_(update_data["dependency_ids"]),
                models.Todo.deleted_at == None
            ).all()
            if len(prerequisites) != len(update_data["dependency_ids"]):
                raise HTTPException(status_code=400, detail="One or more dependencies do not exist or are deleted")
            db_todo.prerequisites = prerequisites
        else:
            db_todo.prerequisites = []
        
        # Recalculate is_blocked based on current status of prerequisites
        db_todo.is_blocked = any(p.status != "Completed" for p in db_todo.prerequisites)

    db_todo.version += 1
    
    # Handle status change side effects
    if "status" in update_data and update_data["status"] != old_status:
        # Handle recurrence if status changed to Completed
        if update_data["status"] == "Completed":
            handle_recurrence(db, db_todo)
    
    db.commit()
    db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: uuid.UUID, version: int):
    db_todo = get_todo(db, todo_id)
    if not db_todo:
        return None
    
    if db_todo.version != version:
        raise VersionMismatchError("Task version mismatch")
    
    # Soft delete
    from datetime import datetime
    db_todo.deleted_at = datetime.utcnow()
    db.commit()
    return db_todo
