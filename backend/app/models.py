import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey, func, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column("dependent_task_id", UUID(as_uuid=True), ForeignKey("todos.id"), primary_key=True),
    Column("prerequisite_task_id", UUID(as_uuid=True), ForeignKey("todos.id"), primary_key=True),
)

class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Not Started", index=True)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium", index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recurrence_anchor: Mapped[str] = mapped_column(String(50), default="DUE_DATE")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Self-referential many-to-many relationship
    prerequisites: Mapped[List["Todo"]] = relationship(
        "Todo",
        secondary=task_dependencies,
        primaryjoin="Todo.id == task_dependencies.c.dependent_task_id",
        secondaryjoin="Todo.id == task_dependencies.c.prerequisite_task_id",
        back_populates="dependents",
    )
    dependents: Mapped[List["Todo"]] = relationship(
        "Todo",
        secondary=task_dependencies,
        primaryjoin="Todo.id == task_dependencies.c.prerequisite_task_id",
        secondaryjoin="Todo.id == task_dependencies.c.dependent_task_id",
        back_populates="prerequisites",
    )
