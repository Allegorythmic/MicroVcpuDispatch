from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_workflow_config_from_file
from .runner import run_workflow


def run_workflow_cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML workflow config")
    args = parser.parse_args()

    cfg = load_workflow_config_from_file(Path(args.config))
    result = run_workflow(cfg)
    print(result)

