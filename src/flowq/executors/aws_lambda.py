from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import boto3  # type: ignore
except Exception:  # pragma: no cover - optional dep
    boto3 = None  # type: ignore


class LambdaDispatcher:
    def __init__(self, *, client: Optional[Any] = None) -> None:
        if client is not None:
            self.client = client
        elif boto3 is not None:
            self.client = boto3.client("lambda")
        else:
            raise RuntimeError("boto3 not installed; install with `pip install flowq[aws]`.")

    def invoke(self, *, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.invoke(FunctionName=function_name, Payload=bytes(str(payload), "utf-8"))
        return {"StatusCode": response.get("StatusCode")}

