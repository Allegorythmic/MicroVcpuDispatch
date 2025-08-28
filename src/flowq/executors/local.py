from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..models import Flow, Task


class LocalExecutor:
    def __init__(self) -> None:
        self.queue: List[Tuple[str, Task, Dict[str, Any]]] = []

    def run_task(self, task_obj: Task, *, params: Optional[Dict[str, Any]] = None) -> Any:
        params = params or {}
        return task_obj.run(**params)

    def run_flow(self, flow: Flow, *, params: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        params = params or {}
        flow.validate()
        results: Dict[str, Any] = {}

        for task_name in flow.topological_order():
            task_obj = flow.tasks[task_name]
            arg_values = params.get(task_name, {})
            self.queue.append((task_name, task_obj, arg_values))

        while self.queue:
            name, task_obj, arg_values = self.queue.pop(0)
            results[name] = task_obj.run(**arg_values)

        return results

