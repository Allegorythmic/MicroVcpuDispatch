from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError
import yaml


class Mode(str, Enum):
    LOCAL = "LOCAL"
    PROD = "PROD"


class StepConfig(BaseModel):
    name: str = Field(..., description="Logical step name")
    task: str = Field(..., description="Registered task identifier")
    params: Dict[str, Any] = Field(default_factory=dict)


class WorkflowConfig(BaseModel):
    mode: Mode = Field(default=Mode.LOCAL)
    input_path: str = Field(..., description="Local path or s3 URI")
    output_path: Optional[str] = Field(default=None, description="Where to write outputs")
    steps: List[StepConfig]

    @property
    def is_prod(self) -> bool:
        return self.mode == Mode.PROD


def load_workflow_config_from_yaml(yaml_content: str) -> WorkflowConfig:
    data = yaml.safe_load(yaml_content)
    try:
        return WorkflowConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid workflow YAML: {exc}") from exc


def load_workflow_config_from_file(path: str | Path) -> WorkflowConfig:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return load_workflow_config_from_yaml(content)

