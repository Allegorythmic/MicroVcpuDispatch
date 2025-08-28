#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    rng = np.random.default_rng(42)
    n = 1000
    feature_1 = rng.normal(loc=0.0, scale=1.0, size=n)
    feature_2 = rng.normal(loc=2.0, scale=1.5, size=n)
    logits = 0.8 * feature_1 - 0.6 * feature_2 + 0.2
    probs = 1 / (1 + np.exp(-logits))
    target = (rng.uniform(size=n) < probs).astype(int)

    df = pd.DataFrame({
        "feature_1": feature_1,
        "feature_2": feature_2,
        "target": target,
    })

    out_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "example.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Wrote {out_path} with shape {df.shape}")


if __name__ == "__main__":
    main()

