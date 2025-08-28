from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow.parquet as pq

from ..registry import registry


@dataclass
class TaskResult:
    data: Optional[pd.DataFrame] = None
    artifacts: Dict[str, Any] = None


def _read_parquet_any(path: str) -> pd.DataFrame:
    if path.startswith("s3://"):
        table = pq.read_table(path)
        return table.to_pandas()
    return pd.read_parquet(path)


@registry.register("ingest_parquet")
def ingest_parquet(input_path: str, **_: Any) -> TaskResult:
    df = _read_parquet_any(input_path)
    return TaskResult(data=df, artifacts={"rows": len(df), "cols": list(df.columns)})


def _apply_transform(df: pd.DataFrame, spec: Dict[str, Any]) -> pd.DataFrame:
    op = spec.get("op")
    if op == "select_columns":
        columns: List[str] = spec["columns"]
        return df[columns]
    if op == "dropna":
        return df.dropna()
    if op == "filter_gt":
        column = spec["column"]
        threshold = spec["threshold"]
        return df[df[column] > threshold]
    raise ValueError(f"Unknown transform op: {op}")


@registry.register("apply_transforms")
def apply_transforms(data: pd.DataFrame, transforms: List[Dict[str, Any]] | None = None, **_: Any) -> TaskResult:
    df = data.copy()
    for spec in transforms or []:
        df = _apply_transform(df, spec)
    return TaskResult(data=df, artifacts={"rows": len(df)})


@registry.register("train_random_forest")
def train_random_forest(data: pd.DataFrame, target: str, **_: Any) -> TaskResult:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    X = data.drop(columns=[target])
    y = data[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    acc = float(accuracy_score(y_test, preds))
    return TaskResult(data=data, artifacts={"model": clf, "accuracy": acc})


@registry.register("summarize_results")
def summarize_results(artifacts: Dict[str, Any], output_path: Optional[str] = None, **_: Any) -> TaskResult:
    summary = {k: v for k, v in artifacts.items() if k != "model"}
    if output_path:
        import json, os
        os.makedirs(output_path, exist_ok=True)
        with open(f"{output_path}/summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    return TaskResult(artifacts=summary)

