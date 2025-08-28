from __future__ import annotations

from typing import Optional

from .config import Settings
from .dispatchers import LocalDispatcher
from .dispatchers import ECSDispatcher as _ECS
from .dispatchers import LambdaDispatcher as _Lambda
from .dispatchers import StepFunctionsDispatcher as _SFN
from .models import QueueMessage, Task
from .queues import FileQueue, InMemoryQueue, QueueBackend


def _make_queue(settings: Settings) -> QueueBackend:
	backend = settings.queue_backend
	if backend == "memory":
		return InMemoryQueue()
	if backend == "file":
		if not settings.file_queue_path:
			raise ValueError("file_queue_path required for file backend")
		return FileQueue(settings.file_queue_path)
	if backend == "sqs":
		from .queues.sqs import SQSQueue  # lazy import
		if not settings.sqs_queue_url:
			raise ValueError("sqs_queue_url required for sqs backend")
		return SQSQueue(settings.sqs_queue_url)
	raise ValueError(f"Unknown queue backend: {backend}")


def _make_dispatcher(kind: str, settings: Settings):
	if kind == "local":
		return LocalDispatcher()
	if kind == "lambda":
		if _Lambda is None:
			raise RuntimeError("AWS extras not installed")
		return _Lambda(settings.aws_region)
	if kind == "ecs":
		if _ECS is None:
			raise RuntimeError("AWS extras not installed")
		return _ECS(settings.aws_region)
	if kind == "sfn":
		if _SFN is None:
			raise RuntimeError("AWS extras not installed")
		return _SFN(settings.aws_region)
	raise ValueError(f"Unknown dispatcher: {kind}")


def process_one(queue: QueueBackend, settings: Settings) -> Optional[QueueMessage]:
	msg = queue.receive()
	if not msg:
		return None
	dispatcher_kind = msg.task.dispatcher or settings.default_dispatcher
	dispatcher = _make_dispatcher(dispatcher_kind, settings)
	dispatcher.dispatch(msg.task)
	queue.delete(msg)
	return msg

