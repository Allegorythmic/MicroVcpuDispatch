from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import boto3  # type: ignore
except Exception:  # pragma: no cover
    boto3 = None  # type: ignore


class ECSDispatcher:
    def __init__(self, *, client: Optional[Any] = None) -> None:
        if client is not None:
            self.client = client
        elif boto3 is not None:
            self.client = boto3.client("ecs")
        else:
            raise RuntimeError("boto3 not installed; install with `pip install flowq[aws]`.")

    def run_task(
        self,
        *,
        cluster: str,
        task_definition: str,
        launch_type: str = "FARGATE",
        subnets: Optional[list[str]] = None,
        security_groups: Optional[list[str]] = None,
        env_vars: Dict[str, str] = {},
    ) -> Dict[str, Any]:
        overrides = {
            "containerOverrides": [
                {
                    "name": "app",
                    "environment": [{"name": k, "value": v} for k, v in env_vars.items()],
                }
            ]
        }
        network = {
            "awsvpcConfiguration": {
                "subnets": subnets or [],
                "securityGroups": security_groups or [],
                "assignPublicIp": "ENABLED",
            }
        }
        response = self.client.run_task(
            cluster=cluster,
            taskDefinition=task_definition,
            launchType=launch_type,
            overrides=overrides,
            networkConfiguration=network,
        )
        return {"tasks": response.get("tasks", [])}

