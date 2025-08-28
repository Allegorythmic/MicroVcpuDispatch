from __future__ import annotations

from typing import Any, Callable, Dict


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if name in self._tasks:
                raise ValueError(f"Task '{name}' already registered")
            self._tasks[name] = func
            return func
        return decorator

    def get(self, name: str) -> Callable[..., Any]:
        if name not in self._tasks:
            raise KeyError(f"Task '{name}' not found in registry")
        return self._tasks[name]

    def names(self) -> list[str]:
        return sorted(self._tasks.keys())


registry = TaskRegistry()

