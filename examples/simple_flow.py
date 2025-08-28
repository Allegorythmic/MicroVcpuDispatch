from __future__ import annotations

from flowq.models import Flow, task


@task()
def task_fetch() -> str:
    return "data"


@task()
def task_transform(data: str = "data") -> str:
    return data.upper()


def build_flow() -> Flow:
    f = Flow()
    f.add_task(task_fetch)
    f.add_task(task_transform)
    f.add_dependency("task_fetch", "task_transform")
    return f

