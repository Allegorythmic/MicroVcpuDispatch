from __future__ import annotations

import json
import os
from typing import Any, Dict

try:
	import boto3  # type: ignore
except Exception as exc:  # pragma: no cover - optional
	boto3 = None  # type: ignore

from ..models import Task
from .base import Dispatcher


def _ensure_boto3() -> None:
	if boto3 is None:
		raise RuntimeError("boto3 not installed. Install with 'pip install flowq[aws]'.")


class LambdaDispatcher(Dispatcher):
	def __init__(self, region: str | None = None) -> None:
		_ensure_boto3()
		self._client = boto3.client("lambda", region_name=region or os.getenv("AWS_REGION"))

	def dispatch(self, task: Task) -> None:
		function_name = task.options.get("function_name")
		if not function_name:
			raise ValueError("Lambda dispatcher requires option 'function_name'")
		self._client.invoke(
			FunctionName=function_name,
			InvocationType="Event",
			Payload=json.dumps(task.payload).encode("utf-8"),
		)


class ECSDispatcher(Dispatcher):
	def __init__(self, region: str | None = None) -> None:
		_ensure_boto3()
		self._ecs = boto3.client("ecs", region_name=region or os.getenv("AWS_REGION"))

	def dispatch(self, task: Task) -> None:
		cluster = task.options.get("cluster")
		task_definition = task.options.get("task_definition")
		subnets = task.options.get("subnets") or []
		security_groups = task.options.get("security_groups") or []
		launch_type = task.options.get("launch_type", "FARGATE")
		assign_public_ip = task.options.get("assign_public_ip", True)
		if not cluster or not task_definition:
			raise ValueError("ECS dispatcher requires 'cluster' and 'task_definition'")
		overrides = task.options.get("overrides") or {
			"containerOverrides": [
				{"name": task.options.get("container_name", "app"), "environment": [
					{"name": "PAYLOAD", "value": json.dumps(task.payload)}
				]},
			]
		}
		self._ecs.run_task(
			cluster=cluster,
			taskDefinition=task_definition,
			launchType=launch_type,
			networkConfiguration={
				"awsvpcConfiguration": {
					"subnets": subnets,
					"securityGroups": security_groups,
					"assignPublicIp": "ENABLED" if assign_public_ip else "DISABLED",
				}
			},
			overrides=overrides,
		)


class StepFunctionsDispatcher(Dispatcher):
	def __init__(self, region: str | None = None) -> None:
		_ensure_boto3()
		self._sfn = boto3.client("stepfunctions", region_name=region or os.getenv("AWS_REGION"))

	def dispatch(self, task: Task) -> None:
		state_machine_arn = task.options.get("state_machine_arn")
		if not state_machine_arn:
			raise ValueError("Step Functions dispatcher requires 'state_machine_arn'")
		name = task.name
		self._sfn.start_execution(
			stateMachineArn=state_machine_arn,
			name=name,
			input=json.dumps(task.payload),
		)

