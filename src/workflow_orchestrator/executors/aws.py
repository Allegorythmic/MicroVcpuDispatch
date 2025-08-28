from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import boto3


class ECSExecutor:
    def __init__(
        self,
        cluster: str,
        task_definition: str,
        container_name: Optional[str] = None,
        subnets: Optional[List[str]] = None,
        security_groups: Optional[List[str]] = None,
        assign_public_ip: bool = False,
        region_name: Optional[str] = None,
    ) -> None:
        self.cluster = cluster
        self.task_definition = task_definition
        self.container_name = container_name
        self.subnets = subnets or []
        self.security_groups = security_groups or []
        self.assign_public_ip = assign_public_ip
        self.region_name = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
        self.ecs = boto3.client("ecs", region_name=self.region_name)

    def run(self, steps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        # Dispatch one ECS task per workflow with steps/context as JSON env var
        overrides_env = [
            {"name": "WORKFLOW_STEPS", "value": json.dumps(steps)},
            {"name": "WORKFLOW_CONTEXT", "value": json.dumps(_jsonify_context(context))},
        ]
        container_overrides: Dict[str, Any] = {"environment": overrides_env}
        if self.container_name:
            container_overrides["name"] = self.container_name
        run_kwargs: Dict[str, Any] = {
            "cluster": self.cluster,
            "taskDefinition": self.task_definition,
            "overrides": {"containerOverrides": [container_overrides]},
            "launchType": "FARGATE",
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": self.subnets,
                    "securityGroups": self.security_groups,
                    "assignPublicIp": "ENABLED" if self.assign_public_ip else "DISABLED",
                }
            },
        }
        resp = self.ecs.run_task(**run_kwargs)
        failures = resp.get("failures")
        if failures:
            raise RuntimeError(f"ECS run_task failures: {failures}")
        return context


class LambdaExecutor:
    def __init__(self, function_name: str, region_name: Optional[str] = None) -> None:
        self.function_name = function_name
        self.region_name = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
        self.lambda_client = boto3.client("lambda", region_name=self.region_name)

    def run(self, steps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "steps": steps,
            "context": _jsonify_context(context),
        }
        resp = self.lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType="Event",  # async
            Payload=json.dumps(payload).encode("utf-8"),
        )
        status = resp.get("StatusCode")
        if status and status >= 400:
            raise RuntimeError(f"Lambda invoke failed with status {status}")
        return context


def _jsonify_context(context: Dict[str, Any]) -> Dict[str, Any]:
    serializable: Dict[str, Any] = {}
    for k, v in context.items():
        if k == "data":
            # do not try to serialize DataFrame; pass metadata only
            if hasattr(v, "shape"):
                serializable[k] = {"type": "dataframe", "shape": getattr(v, "shape", None)}
            else:
                serializable[k] = None
        else:
            try:
                json.dumps(v)
                serializable[k] = v
            except Exception:
                serializable[k] = str(v)
    return serializable

