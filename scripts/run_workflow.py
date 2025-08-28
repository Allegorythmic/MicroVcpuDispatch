#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from workflow_orchestrator.config import load_workflow_config_from_file
from workflow_orchestrator.runner import run_workflow


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML workflow config")
    args = parser.parse_args()

    cfg = load_workflow_config_from_file(Path(args.config))
    result = run_workflow(cfg)
    print({k: (str(v)[:200] if k != "data" else f"DataFrame[{v.shape}]") for k, v in result.items()})


if __name__ == "__main__":
    main()

