import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class TodoBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = "Not Started"
    priority: str = "Medium"
    due_date: Optional[datetime] = None
    recurrence_rule: Optional[str] = None
    recurrence_anchor: str = "DUE_DATE"

class TodoCreate(TodoBase):
    dependency_ids: Optional[List[uuid.UUID]] = []

class TodoStatusUpdate(BaseModel):
    status: str
    version: int

class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    recurrence_rule: Optional[str] = None
    recurrence_anchor: Optional[str] = None
    dependency_ids: Optional[List[uuid.UUID]] = None
    version: int

class Todo(TodoBase):
    id: uuid.UUID
    is_blocked: bool
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
