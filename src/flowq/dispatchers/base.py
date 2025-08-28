from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Task


class Dispatcher(ABC):
	@abstractmethod
	def dispatch(self, task: Task) -> None:
		...

