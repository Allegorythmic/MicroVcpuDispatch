from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    environment: str = os.getenv("FLOWQ_ENV", "local")  # 'local' or 'aws'

