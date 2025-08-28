from __future__ import annotations

import queue
import threading
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import os
from ..config import WorkflowConfig, load_workflow_config_from_yaml, Mode
from ..runner import run_workflow
from ..executors.aws import ECSExecutor, LambdaExecutor
from ..monitoring.aws_metrics import get_ecs_vcpu_in_use, get_lambda_concurrency


class SubmitRequest(BaseModel):
    yaml_config: str


class Metrics(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int
    ecs_vcpu_in_use: int = 0
    lambda_concurrency_in_use: int = 0
    ecs_vcpu_limit: int = 0
    lambda_concurrency_limit: int = 0


app = FastAPI(title="Workflow Dispatcher")


job_queue: "queue.Queue[WorkflowConfig]" = queue.Queue()
running_jobs = 0
completed_jobs = 0
failed_jobs = 0
metrics_lock = threading.Lock()
paused_flag = False


def should_throttle_for_prod(cfg: WorkflowConfig) -> bool:
    backend = os.getenv("WORKFLOW_BACKEND", "ECS").upper()
    if backend == "ECS":
        limit = int(os.getenv("ECS_VCPU_LIMIT", "0") or 0)
        cluster = os.getenv("ECS_CLUSTER")
        if limit and cluster:
            try:
                in_use = get_ecs_vcpu_in_use(cluster)
                return in_use >= limit
            except Exception:
                return False
    if backend == "LAMBDA":
        limit = int(os.getenv("LAMBDA_CONCURRENCY_LIMIT", "0") or 0)
        if limit:
            try:
                in_use = get_lambda_concurrency()
                return in_use >= limit
            except Exception:
                return False
    return False


def worker_loop() -> None:
    global running_jobs, completed_jobs, failed_jobs
    while True:
        cfg = job_queue.get()
        # pause handling
        with metrics_lock:
            is_paused = paused_flag
        if is_paused:
            # Requeue and wait briefly
            job_queue.put(cfg)
            time.sleep(1.0)
            job_queue.task_done()
            continue
        # throttle handling for PROD
        if cfg.mode == Mode.PROD and should_throttle_for_prod(cfg):
            job_queue.put(cfg)
            time.sleep(2.0)
            job_queue.task_done()
            continue
        with metrics_lock:
            running_jobs += 1
        try:
            # Decide backend
            if cfg.mode == Mode.PROD:
                backend = os.getenv("WORKFLOW_BACKEND", "ECS").upper()
                if backend == "ECS":
                    cluster = os.getenv("ECS_CLUSTER", "default")
                    task_def = os.getenv("ECS_TASK_DEFINITION", "")
                    subnets = os.getenv("ECS_SUBNETS", "").split(",") if os.getenv("ECS_SUBNETS") else []
                    sec_groups = os.getenv("ECS_SECURITY_GROUPS", "").split(",") if os.getenv("ECS_SECURITY_GROUPS") else []
                    assign_ip = os.getenv("ECS_ASSIGN_PUBLIC_IP", "false").lower() == "true"
                    executor = ECSExecutor(cluster=cluster, task_definition=task_def, subnets=subnets, security_groups=sec_groups, assign_public_ip=assign_ip)
                    executor.run([s.model_dump() for s in cfg.steps], {"input_path": cfg.input_path, "output_path": cfg.output_path})
                elif backend == "LAMBDA":
                    fn = os.getenv("LAMBDA_FUNCTION", "")
                    executor = LambdaExecutor(function_name=fn)
                    executor.run([s.model_dump() for s in cfg.steps], {"input_path": cfg.input_path, "output_path": cfg.output_path})
                else:
                    # Fallback to local execution
                    run_workflow(cfg)
            else:
                run_workflow(cfg)
            with metrics_lock:
                completed_jobs += 1
        except Exception:
            with metrics_lock:
                failed_jobs += 1
        finally:
            with metrics_lock:
                running_jobs -= 1
            job_queue.task_done()


threading.Thread(target=worker_loop, daemon=True).start()


@app.post("/submit")
def submit(req: SubmitRequest) -> Dict[str, Any]:
    try:
        cfg = load_workflow_config_from_yaml(req.yaml_config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    job_queue.put(cfg)
    return {"status": "queued"}


@app.post("/control/pause")
def pause_queue() -> Dict[str, Any]:
    global paused_flag
    with metrics_lock:
        paused_flag = True
    return {"status": "paused"}


@app.post("/control/resume")
def resume_queue() -> Dict[str, Any]:
    global paused_flag
    with metrics_lock:
        paused_flag = False
    return {"status": "resumed"}


@app.get("/metrics", response_model=Metrics)
def get_metrics() -> Metrics:
    ecs_limit = int(os.getenv("ECS_VCPU_LIMIT", "0") or 0)
    lambda_limit = int(os.getenv("LAMBDA_CONCURRENCY_LIMIT", "0") or 0)
    ecs_cluster = os.getenv("ECS_CLUSTER")
    ecs_in_use = 0
    if ecs_cluster:
        try:
            ecs_in_use = get_ecs_vcpu_in_use(ecs_cluster)
        except Exception:
            ecs_in_use = 0
    lambda_in_use = 0
    try:
        lambda_in_use = get_lambda_concurrency()
    except Exception:
        lambda_in_use = 0
    with metrics_lock:
        return Metrics(
            queued=job_queue.qsize(),
            running=running_jobs,
            completed=completed_jobs,
            failed=failed_jobs,
            ecs_vcpu_in_use=ecs_in_use,
            lambda_concurrency_in_use=lambda_in_use,
            ecs_vcpu_limit=ecs_limit,
            lambda_concurrency_limit=lambda_limit,
        )

