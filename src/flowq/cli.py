from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .config import Config
from .runner import Runner
from .utils import import_object


def _parse_kv_pairs(pairs: list[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError("Params must be key=value")
        k, v = item.split("=", 1)
        try:
            result[k] = json.loads(v)
        except json.JSONDecodeError:
            result[k] = v
    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog="flowq")
    sub = parser.add_subparsers(dest="command", required=True)

    p_flow = sub.add_parser("run-flow", help="Run a flow locally")
    p_flow.add_argument("flow_ref", help="module:function that returns a Flow")
    p_flow.add_argument("--env", default=None)

    p_task = sub.add_parser("run-task", help="Run a task locally or dispatch to AWS")
    p_task.add_argument("task_ref", help="module:task_object or module:function to wrap")
    p_task.add_argument("--env", default=None)
    p_task.add_argument("--target", choices=["lambda", "ecs", "sfn"], default=None)
    p_task.add_argument("--param", action="append", default=[], help="key=value pairs; can be JSON values")
    p_task.add_argument("--function-name", help="Lambda function name")
    p_task.add_argument("--cluster")
    p_task.add_argument("--task-definition")
    p_task.add_argument("--state-machine-arn")

    args = parser.parse_args()
    if args.env:
        config = Config(environment=args.env)
    else:
        config = Config()
    runner = Runner(config)

    if args.command == "run-flow":
        build_flow = import_object(args.flow_ref)
        flow = build_flow()
        results = runner.run_flow(flow)
        print(json.dumps(results, default=str))
        return

    if args.command == "run-task":
        obj = import_object(args.task_ref)
        # If the imported obj is a function, expose .name and .run-compatible API
        if callable(obj) and not hasattr(obj, "run"):
            from .models import Task

            task_obj = Task(name=getattr(obj, "__name__", "task"), func=obj)
        else:
            task_obj = obj
        params = _parse_kv_pairs(args.param)
        kwargs: Dict[str, Any] = {}
        if args.target == "lambda":
            kwargs["function_name"] = args.function_name
        elif args.target == "ecs":
            kwargs.update({
                "cluster": args.cluster,
                "task_definition": args.task_definition,
            })
        elif args.target == "sfn":
            kwargs["state_machine_arn"] = args.state_machine_arn

        result = runner.run_task(task_obj, params=params, target=args.target, **kwargs)
        print(json.dumps(result, default=str))
        return


if __name__ == "__main__":
    main()

