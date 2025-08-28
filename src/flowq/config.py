from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field


class Settings(BaseModel):
	environment: str = Field(default=os.getenv("FLOWQ_ENV", "dev"))
	queue_backend: str = Field(default=os.getenv("FLOWQ_QUEUE_BACKEND", "memory"))
	aws_region: Optional[str] = Field(default=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"))

	# File queue options
	file_queue_path: Optional[str] = Field(default=os.getenv("FLOWQ_FILE_QUEUE_PATH"))

	# SQS
	sqs_queue_url: Optional[str] = Field(default=os.getenv("FLOWQ_SQS_QUEUE_URL"))

	# Dispatcher defaults
	default_dispatcher: str = Field(default=os.getenv("FLOWQ_DEFAULT_DISPATCHER", "local"))

	class Config:
		frozen = True


def _load_yaml(path: Path) -> Dict[str, Any]:
	if not path.exists():
		return {}
	with path.open("r", encoding="utf-8") as f:
		data = yaml.safe_load(f) or {}
		if not isinstance(data, dict):
			return {}
		return data


def load_settings(config_path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> Settings:
	"""Load settings from YAML (if provided), env, and dict overrides (highest priority)."""
	candidate_path = (
		Path(config_path)
		if config_path
		else Path(os.getenv("FLOWQ_CONFIG", "flowq.yaml"))
	)
	yaml_data = _load_yaml(candidate_path)
	merged: Dict[str, Any] = {**yaml_data}
	if overrides:
		merged.update({k: v for k, v in overrides.items() if v is not None})
	return Settings(**merged)

