from __future__ import annotations

from pathlib import Path

import pandas as pd

from workflow_orchestrator.config import load_workflow_config_from_yaml
from workflow_orchestrator.runner import run_workflow


def test_local_run_smoke(tmp_path: Path) -> None:
    df = pd.DataFrame({"feature_1": [0, 1], "feature_2": [2, 3], "target": [0, 1]})
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "example.parquet").write_bytes(b"")
    df.to_parquet(data_dir / "example.parquet", index=False)
    yml = f"""
mode: LOCAL
input_path: {str(data_dir / 'example.parquet')}
output_path: {str(tmp_path)}
steps:
  - name: ingest
    task: ingest_parquet
  - name: transform
    task: apply_transforms
    params:
      transforms:
        - op: select_columns
          columns: [feature_1, feature_2, target]
  - name: train
    task: train_random_forest
    params:
      target: target
  - name: summarize
    task: summarize_results
"""
    cfg = load_workflow_config_from_yaml(yml)
    result = run_workflow(cfg)
    assert "artifacts" in result
    assert "accuracy" in result["artifacts"]
