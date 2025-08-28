from __future__ import annotations

from typing import Any, Dict

from .config import WorkflowConfig, Mode
from .executors.local import LocalExecutor
from . import tasks  # ensure task modules are imported and registered


def run_workflow(config: WorkflowConfig) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "input_path": config.input_path,
        "output_path": config.output_path,
        "artifacts": {},
    }
    steps = [s.model_dump() for s in config.steps]

    if config.mode == Mode.LOCAL:
        executor = LocalExecutor()
        context = executor.run(steps, context)
        return context

    # PROD mode should dispatch to AWS via dispatcher; here we simply raise
    raise NotImplementedError("PROD mode execution is handled by the dispatcher service")

