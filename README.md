## Python Workflow Orchestration Framework

This project provides a lightweight workflow orchestration framework with a dispatcher microservice and real-time monitoring dashboard.

### Features
- LOCAL execution on CPU cores
- PROD stubs for AWS ECS and AWS Lambda dispatch
- YAML-defined pipelines (ingest → transform → train → summarize)
- FastAPI dispatcher with simple scheduling and resource throttling
- Streamlit dashboard for metrics

### Quickstart
1) Install dependencies:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Run a local workflow from example YAML:
```bash
python scripts/run_workflow.py --config examples/workflow.yaml
```

3) Start the dispatcher API:
```bash
uvicorn workflow_orchestrator.dispatcher.app:app --reload --host 0.0.0.0 --port 8000
```

4) Start the dashboard:
```bash
streamlit run streamlit_app.py
```

### YAML Config Outline
```yaml
mode: LOCAL  # or PROD
input_path: ./data/example.parquet  # or s3://bucket/key in PROD
output_path: ./outputs
steps:
  - name: ingest
    task: ingest_parquet
  - name: transform
    task: apply_transforms
    params:
      transforms:
        - { op: select_columns, columns: ["feature_1", "feature_2", "target"] }
        - { op: dropna }
  - name: train
    task: train_random_forest
    params:
      target: target
  - name: summarize
    task: summarize_results
```

### Notes
- AWS executors are provided as stubs for integration with ECS/Lambda.
- Streamlit dashboard polls the dispatcher metrics endpoint.
