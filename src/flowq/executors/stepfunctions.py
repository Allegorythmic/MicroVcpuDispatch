from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import boto3  # type: ignore
except Exception:  # pragma: no cover
    boto3 = None  # type: ignore


class StepFunctionsDispatcher:
    def __init__(self, *, client: Optional[Any] = None) -> None:
        if client is not None:
            self.client = client
        elif boto3 is not None:
            self.client = boto3.client("stepfunctions")
        else:
            raise RuntimeError("boto3 not installed; install with `pip install flowq[aws]`.")

    def start_execution(self, *, state_machine_arn: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.start_execution(stateMachineArn=state_machine_arn, input=str(input_data))
        return {"executionArn": response.get("executionArn")}

