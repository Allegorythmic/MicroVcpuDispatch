from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models import QueueMessage, Receipt, Task
from .base import QueueBackend


class FileQueue(QueueBackend):
	def __init__(self, path: str) -> None:
		self._path = Path(path)
		self._path.parent.mkdir(parents=True, exist_ok=True)
		self._path.touch(exist_ok=True)

	def enqueue(self, task: Task) -> None:
		with self._path.open("a", encoding="utf-8") as f:
			f.write(task.model_dump_json() + "\n")

	def receive(self, wait_seconds: int = 0) -> Optional[QueueMessage]:
		# naive implementation: read first line, then rewrite file without it
		lines = self._path.read_text(encoding="utf-8").splitlines()
		if not lines:
			return None
		first = lines[0]
		rest = lines[1:]
		self._path.write_text("\n".join(rest) + ("\n" if rest else ""), encoding="utf-8")
		data = json.loads(first)
		task = Task(**data)
		return QueueMessage(task=task, receipt=Receipt(id=None))

	def delete(self, receipt: QueueMessage) -> None:
		return None

