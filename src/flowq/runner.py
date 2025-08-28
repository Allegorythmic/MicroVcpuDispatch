from __future__ import annotations

from typing import Any, Dict, Optional

from .config import Config
from .models import Flow, Task
from .executors.local import LocalExecutor


class Runner:
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()

    def run_flow(self, flow: Flow, *, params: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        if self.config.environment == "local":
            return LocalExecutor().run_flow(flow, params=params)
        raise NotImplementedError("Flow execution to AWS is not implemented; use Step Functions dispatcher externally.")

    def run_task(
        self,
        task_obj: Task,
        *,
        params: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        env = self.config.environment
        if env == "local" or not target:
            return LocalExecutor().run_task(task_obj, params=params)

        if env == "aws":
            if target == "lambda":
                from .executors.aws_lambda import LambdaDispatcher

                dispatcher = LambdaDispatcher()
                return dispatcher.invoke(function_name=kwargs.get("function_name"), payload=params or {})
            if target == "ecs":
                from .executors.ecs import ECSDispatcher

                dispatcher = ECSDispatcher()
                return dispatcher.run_task(**kwargs, env_vars=params or {})
            if target == "sfn":
                from .executors.stepfunctions import StepFunctionsDispatcher

                dispatcher = StepFunctionsDispatcher()
                return dispatcher.start_execution(**kwargs, input_data=params or {})
            raise ValueError(f"Unknown AWS target: {target}")

        raise ValueError(f"Unknown environment: {env}")

