from __future__ import annotations

from typing import Any, Dict, List


class ECSExecutor:
    def __init__(self, cluster: str, task_definition: str, subnets: List[str] | None = None) -> None:
        self.cluster = cluster
        self.task_definition = task_definition
        self.subnets = subnets or []

    def run(self, steps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: integrate with boto3 ECS to run a task per step or per workflow
        raise NotImplementedError("ECSExecutor not yet implemented")


class LambdaExecutor:
    def __init__(self, function_name: str) -> None:
        self.function_name = function_name

    def run(self, steps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: integrate with boto3 Lambda invoke for each step
        raise NotImplementedError("LambdaExecutor not yet implemented")

