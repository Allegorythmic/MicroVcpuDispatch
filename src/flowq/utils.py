from __future__ import annotations

import importlib
from typing import Any


def import_object(path: str) -> Any:
    """Import an object from a string like 'module.sub:attr'."""
    if ":" not in path:
        raise ValueError("Path must be in form 'module:attr'")
    module_name, attr_name = path.split(":", 1)
    module = importlib.import_module(module_name)
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise AttributeError(f"{attr_name} not found in module {module_name}") from exc

