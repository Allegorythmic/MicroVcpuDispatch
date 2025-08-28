from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple


TaskCallable = Callable[..., Any]


@dataclass
class Task:
    name: str
    func: TaskCallable

    def run(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)


def task(name: Optional[str] = None) -> Callable[[TaskCallable], Task]:
    def decorator(func: TaskCallable) -> Task:
        task_name = name or func.__name__
        return Task(name=task_name, func=func)

    return decorator


@dataclass
class Flow:
    """A directed acyclic graph of tasks.

    Nodes are task names; edges are (upstream -> downstream).
    """

    tasks: Dict[str, Task] = field(default_factory=dict)
    edges: Set[Tuple[str, str]] = field(default_factory=set)

    def add_task(self, task_obj: Task) -> None:
        if task_obj.name in self.tasks:
            raise ValueError(f"Task with name '{task_obj.name}' already exists")
        self.tasks[task_obj.name] = task_obj

    def add_dependency(self, upstream: str, downstream: str) -> None:
        if upstream not in self.tasks or downstream not in self.tasks:
            raise KeyError("Dependencies must reference existing tasks")
        if upstream == downstream:
            raise ValueError("Cannot depend on itself")
        self.edges.add((upstream, downstream))

    def upstream_of(self, task_name: str) -> Set[str]:
        return {u for (u, d) in self.edges if d == task_name}

    def downstream_of(self, task_name: str) -> Set[str]:
        return {d for (u, d) in self.edges if u == task_name}

    def topological_order(self) -> List[str]:
        """Kahn's algorithm for topo sort and cycle detection."""
        in_degree: Dict[str, int] = {t: 0 for t in self.tasks}
        for u, d in self.edges:
            in_degree[d] += 1

        ready: List[str] = [t for t, deg in in_degree.items() if deg == 0]
        ordered: List[str] = []
        edges_copy = set(self.edges)

        while ready:
            node = ready.pop(0)
            ordered.append(node)
            for d in list(self.downstream_of(node)):
                if (node, d) in edges_copy:
                    edges_copy.remove((node, d))
                    in_degree[d] -= 1
                    if in_degree[d] == 0:
                        ready.append(d)

        if edges_copy:
            cycle_edges = ", ".join([f"{u}->{d}" for (u, d) in edges_copy])
            raise ValueError(f"Cycle detected in flow: {cycle_edges}")

        return ordered

    def validate(self) -> None:
        if not self.tasks:
            raise ValueError("Flow has no tasks")
        self.topological_order()

