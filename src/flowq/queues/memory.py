from __future__ import annotations

from collections import deque
from typing import Optional

from ..models import QueueMessage, Receipt, Task
from .base import QueueBackend


class InMemoryQueue(QueueBackend):
	def __init__(self) -> None:
		self._queue: deque[Task] = deque()

	def enqueue(self, task: Task) -> None:
		self._queue.append(task)

	def receive(self, wait_seconds: int = 0) -> Optional[QueueMessage]:
		try:
			task = self._queue.popleft()
			return QueueMessage(task=task, receipt=Receipt(id=None))
		except IndexError:
			return None

	def delete(self, receipt: QueueMessage) -> None:
		return None

