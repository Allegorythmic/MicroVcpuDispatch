from __future__ import annotations

from flowq.models import Flow, task
from flowq.executors.local import LocalExecutor


def test_topological_execution():
    @task()
    def a() -> str:
        return "a"

    @task()
    def b() -> str:
        return "b"

    @task()
    def c() -> str:
        return "c"

    flow = Flow()
    for t in (a, b, c):
        flow.add_task(t)
    flow.add_dependency("a", "c")
    flow.add_dependency("b", "c")

    results = LocalExecutor().run_flow(flow)
    assert results["a"] == "a"
    assert results["b"] == "b"
    assert results["c"] == "c"

