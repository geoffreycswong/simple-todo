import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas, background
from .database import engine, get_db

app = FastAPI(title="TODO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/tasks", response_model=schemas.Todo, status_code=status.HTTP_201_CREATED)
def create_task(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db=db, todo=todo)

@app.get("/api/v1/tasks", response_model=List[schemas.Todo])
def read_tasks(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    due_date_before: Optional[datetime] = None,
    due_date_after: Optional[datetime] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    is_deleted: bool = False,
    db: Session = Depends(get_db)
):
    total = crud.count_todos(
        db, status=status, priority=priority, is_blocked=is_blocked,
        due_date_before=due_date_before, due_date_after=due_date_after,
        is_deleted=is_deleted
    )
    tasks = crud.get_todos(
        db,
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        is_blocked=is_blocked,
        due_date_before=due_date_before,
        due_date_after=due_date_after,
        sort_by=sort_by,
        order=order,
        is_deleted=is_deleted
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return tasks

@app.get("/api/v1/tasks/{task_id}", response_model=schemas.Todo)
def read_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=task_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_todo

@app.put("/api/v1/tasks/{task_id}", response_model=schemas.Todo)
def update_task(task_id: uuid.UUID, todo: schemas.TodoUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # Check for status change to trigger background propagation
        db_todo_old = crud.get_todo(db, task_id)
        if not db_todo_old:
             raise HTTPException(status_code=404, detail="Task not found")
        old_status = db_todo_old.status
        
        updated_todo = crud.update_todo(db=db, todo_id=task_id, todo=todo)
        
        if updated_todo.status != old_status:
            background_tasks.add_task(background.propagate_dependency_status, task_id)
            
        return updated_todo
    except crud.VersionMismatchError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.patch("/api/v1/tasks/{task_id}/status", response_model=schemas.Todo)
def update_task_status(task_id: uuid.UUID, status_update: schemas.TodoStatusUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=task_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if db_todo.version != status_update.version:
        raise HTTPException(status_code=409, detail="Task version mismatch")
    
    # Momentum Rule: Rejection only if transitioning INTO "In Progress" while blocked
    if db_todo.status != "In Progress" and status_update.status == "In Progress":
        if db_todo.is_blocked:
            raise HTTPException(
                status_code=422,
                detail="Task is blocked by incomplete prerequisites"
            )
    
    old_status = db_todo.status
    
    # Payload Isolation: only status and version are updated (version handled by update_todo)
    update_data = schemas.TodoUpdate(
        status=status_update.status,
        version=status_update.version
    )
    
    try:
        updated_todo = crud.update_todo(db, todo_id=task_id, todo=update_data)
        
        # Trigger background propagation if status changed
        if updated_todo.status != old_status:
            background_tasks.add_task(background.propagate_dependency_status, task_id)
            
        return updated_todo
    except crud.VersionMismatchError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.delete("/api/v1/tasks/{task_id}", status_code=204)
def delete_task(task_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
    try:
        db_todo = crud.delete_todo(db, todo_id=task_id, version=version)
        if db_todo is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return Response(status_code=204)
    except crud.VersionMismatchError as e:
        raise HTTPException(status_code=409, detail=str(e))

from fastapi.staticfiles import StaticFiles
import os

# At the end of main.py, after all API routes
static_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
