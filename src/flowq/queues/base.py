from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..models import QueueMessage, Task


class QueueBackend(ABC):
	@abstractmethod
	def enqueue(self, task: Task) -> None:
		...

	@abstractmethod
	def receive(self, wait_seconds: int = 0) -> Optional[QueueMessage]:
		...

	@abstractmethod
	def delete(self, receipt: QueueMessage) -> None:
		...

