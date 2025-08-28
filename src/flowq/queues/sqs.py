from __future__ import annotations

import json
import os
from typing import Optional

try:
	import boto3  # type: ignore
except Exception:  # pragma: no cover - optional
	boto3 = None  # type: ignore

from ..models import QueueMessage, Receipt, Task
from .base import QueueBackend


def _ensure_boto3() -> None:
	if boto3 is None:
		raise RuntimeError("boto3 not installed. Install with 'pip install flowq[aws]'.")


class SQSQueue(QueueBackend):
	def __init__(self, queue_url: str, region: str | None = None) -> None:
		_ensure_boto3()
		self._client = boto3.client("sqs", region_name=region or os.getenv("AWS_REGION"))
		self._url = queue_url

	def enqueue(self, task: Task) -> None:
		self._client.send_message(QueueUrl=self._url, MessageBody=task.model_dump_json())

	def receive(self, wait_seconds: int = 10) -> Optional[QueueMessage]:
		resp = self._client.receive_message(
			QueueUrl=self._url,
			MaxNumberOfMessages=1,
			WaitTimeSeconds=wait_seconds,
		)
		messages = resp.get("Messages", [])
		if not messages:
			return None
		m = messages[0]
		body = json.loads(m["Body"]) if isinstance(m.get("Body"), str) else m.get("Body")
		task = Task(**body)
		receipt_handle = m.get("ReceiptHandle")
		receipt = Receipt(id=receipt_handle, raw=m)
		return QueueMessage(task=task, receipt=receipt)

	def delete(self, receipt: QueueMessage) -> None:
		if receipt.receipt and receipt.receipt.id:
			self._client.delete_message(QueueUrl=self._url, ReceiptHandle=receipt.receipt.id)

