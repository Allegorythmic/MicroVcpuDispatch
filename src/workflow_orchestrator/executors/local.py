from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..registry import registry


class LocalExecutor:
    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers

    def run_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        task_name = step["task"]
        params = step.get("params", {})
        func = registry.get(task_name)

        kwargs: Dict[str, Any] = {}
        # Provide common inputs from context
        if "data" in context and "data" not in params:
            if isinstance(context["data"], pd.DataFrame):
                kwargs["data"] = context["data"]
        if "artifacts" in context and "artifacts" not in params:
            kwargs["artifacts"] = context["artifacts"]
        if "input_path" in context and "input_path" not in params:
            kwargs["input_path"] = context["input_path"]
        if "output_path" in context and "output_path" not in params:
            kwargs["output_path"] = context["output_path"]

        result = func(**{**params, **kwargs})

        new_context = dict(context)
        if getattr(result, "data", None) is not None:
            new_context["data"] = result.data
        if getattr(result, "artifacts", None) is not None:
            merged = dict(new_context.get("artifacts", {}))
            merged.update(result.artifacts)
            new_context["artifacts"] = merged
        return new_context

    def run(self, steps: List[Dict[str, Any]], context: Dict[str, Any], parallel: bool = False) -> Dict[str, Any]:
        if not parallel:
            for step in steps:
                context = self.run_step(step, context)
            return context

        # In parallel mode, run independent steps if marked with group ids
        # Steps with the same "group" will run together, then merged sequentially
        grouped: Dict[Optional[str], List[Dict[str, Any]]] = {}
        for step in steps:
            gid = step.get("group")
            grouped.setdefault(gid, []).append(step)

        for gid, batch in grouped.items():
            if len(batch) == 1:
                context = self.run_step(batch[0], context)
                continue
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = [pool.submit(self.run_step, s, context) for s in batch]
                for fut in as_completed(futures):
                    partial = fut.result()
                    # merge partial results
                    if "data" in partial:
                        context["data"] = partial["data"]
                    if "artifacts" in partial:
                        merged = dict(context.get("artifacts", {}))
                        merged.update(partial["artifacts"])
                        context["artifacts"] = merged
        return context

