from __future__ import annotations

import json
from typing import Optional

import typer

from .config import Settings, load_settings
from .models import Task
from .queues import FileQueue, InMemoryQueue
from .worker import process_one, _make_queue


app = typer.Typer(help="flowq CLI")


def _load_settings(config: Optional[str]) -> Settings:
	return load_settings(config_path=config)


def _make_task(name: str, dispatcher: str, payload: str, option: list[str]) -> Task:
	options = {}
	for item in option:
		# key=value
		if "=" not in item:
			raise typer.BadParameter("Options must be key=value")
		k, v = item.split("=", 1)
		options[k] = v
	return Task(name=name, dispatcher=dispatcher, payload=json.loads(payload), options=options)


def _resolve_queue(settings: Settings, queue_backend: Optional[str], file_queue_path: Optional[str]):
	if queue_backend:
		settings = load_settings(overrides={"queue_backend": queue_backend, "file_queue_path": file_queue_path})
	return _make_queue(settings)


@app.command()
def enqueue(
	name: str = typer.Option(..., help="Task name"),
	dispatcher: str = typer.Option("local", help="Dispatcher kind"),
	payload: str = typer.Option("{}", help="JSON payload"),
	option: list[str] = typer.Option([], help="Dispatcher option key=value"),
	config: Optional[str] = typer.Option(None, help="Path to flowq.yaml"),
	queue_backend: Optional[str] = typer.Option(None, help="Queue backend: memory|file|sqs"),
	file_queue_path: Optional[str] = typer.Option(None, help="File path for file backend"),
) -> None:
	settings = _load_settings(config)
	queue = _resolve_queue(settings, queue_backend, file_queue_path)
	task = _make_task(name, dispatcher, payload, option)
	queue.enqueue(task)
	typer.echo("enqueued")


@app.command("worker")
def run_worker(
	once: bool = typer.Option(False, help="Process one task then exit"),
	config: Optional[str] = typer.Option(None, help="Path to flowq.yaml"),
	queue_backend: Optional[str] = typer.Option(None, help="Queue backend: memory|file|sqs"),
	file_queue_path: Optional[str] = typer.Option(None, help="File path for file backend"),
) -> None:
	settings = _load_settings(config)
	queue = _resolve_queue(settings, queue_backend, file_queue_path)
	while True:
		msg = process_one(queue, settings)
		if once:
			break
		if msg is None:
			continue


@app.command("run-flow-local")
def run_flow_local(callable: str, payload: str = typer.Option("{}", help="JSON payload")) -> None:
	from .dispatchers.local import _resolve_callable
	func = _resolve_callable(callable)
	func(**json.loads(payload))

