from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


DispatcherKind = Literal["local", "lambda", "ecs", "sfn"]


class Task(BaseModel):
	name: str
	dispatcher: DispatcherKind = Field(default="local")
	payload: Dict[str, Any] = Field(default_factory=dict)
	options: Dict[str, Any] = Field(default_factory=dict)
	enqueued_at: datetime = Field(default_factory=datetime.utcnow)


class Receipt(BaseModel):
	id: Optional[str] = None
	# Opaque receipt for deletion/ack in remote queues
	raw: Optional[Any] = None


class QueueMessage(BaseModel):
	task: Task
	receipt: Optional[Receipt] = None

