from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3


def get_lambda_concurrency(region_name: Optional[str] = None) -> int:
    region = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=5)
    resp = cloudwatch.get_metric_statistics(
        Namespace="AWS/Lambda",
        MetricName="ConcurrentExecutions",
        StartTime=start,
        EndTime=end,
        Period=60,
        Statistics=["Maximum"],
    )
    datapoints = resp.get("Datapoints", [])
    if not datapoints:
        return 0
    return int(max(dp.get("Maximum", 0) for dp in datapoints))


def get_ecs_vcpu_in_use(cluster_name: str, region_name: Optional[str] = None) -> int:
    region = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    ecs = boto3.client("ecs", region_name=region)
    paginator = ecs.get_paginator("list_tasks")
    vcpu_sum = 0
    for page in paginator.paginate(cluster=cluster_name, desiredStatus="RUNNING"):
        task_arns = page.get("taskArns", [])
        if not task_arns:
            continue
        desc = ecs.describe_tasks(cluster=cluster_name, tasks=task_arns)
        for task in desc.get("tasks", []):
            cpu = 0
            # Try to read CPU units from task overrides or definition
            if task.get("cpu"):
                try:
                    cpu = int(task["cpu"])  # CPU units
                except Exception:
                    cpu = 0
            elif task.get("overrides", {}).get("inferenceAcceleratorOverrides"):
                pass
            if cpu == 0:
                # fall back to task definition CPU via describe_task_definition
                td_arn = task.get("taskDefinitionArn")
                if td_arn:
                    td = ecs.describe_task_definition(taskDefinition=td_arn)
                    cpu_str = td.get("taskDefinition", {}).get("cpu") or "0"
                    try:
                        cpu = int(cpu_str)
                    except Exception:
                        cpu = 0
            vcpu_sum += int(cpu / 1024) if cpu else 0
    return vcpu_sum

