from __future__ import annotations

import importlib
from typing import Callable

from ..models import Task
from .base import Dispatcher


def _resolve_callable(dotted: str) -> Callable[..., None]:
	# format: module.sub:func
	module_name, func_name = dotted.split(":", 1)
	module = importlib.import_module(module_name)
	func = getattr(module, func_name)
	return func


class LocalDispatcher(Dispatcher):
	def dispatch(self, task: Task) -> None:
		callable_spec = task.options.get("callable")
		if not callable_spec:
			raise ValueError("Local dispatcher requires option 'callable' = 'module:function'")
		func = _resolve_callable(callable_spec)
		func(**task.payload)

