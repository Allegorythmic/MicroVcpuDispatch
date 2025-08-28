from __future__ import annotations

import queue
import threading
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..config import WorkflowConfig, load_workflow_config_from_yaml
from ..runner import run_workflow


class SubmitRequest(BaseModel):
    yaml_config: str


class Metrics(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int
    ecs_vcpu_in_use: int = 0
    lambda_concurrency_in_use: int = 0


app = FastAPI(title="Workflow Dispatcher")


job_queue: "queue.Queue[WorkflowConfig]" = queue.Queue()
running_jobs = 0
completed_jobs = 0
failed_jobs = 0
metrics_lock = threading.Lock()


def worker_loop() -> None:
    global running_jobs, completed_jobs, failed_jobs
    while True:
        cfg = job_queue.get()
        with metrics_lock:
            running_jobs += 1
        try:
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


@app.get("/metrics", response_model=Metrics)
def get_metrics() -> Metrics:
    with metrics_lock:
        return Metrics(
            queued=job_queue.qsize(),
            running=running_jobs,
            completed=completed_jobs,
            failed=failed_jobs,
        )

