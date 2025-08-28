flowq
=====

Queue and dispatch Python tasks/flows to AWS (ECS, Lambda, Step Functions) with easy local testing.

Quick start
-----------

1) Install in editable mode:

```bash
python3 -m pip install --break-system-packages -e .[aws]
```

2) Enqueue a local function call and run worker (single process demo):

```bash
flowq enqueue --name say-hello --dispatcher local --option callable=examples.hello:say_hello --payload '{"name":"World"}'
flowq worker --once
```

3) Use a file-backed queue across processes for local dev:

```bash
flowq enqueue --queue-backend file --file-queue-path ./.flowq/queue.jsonl \
  --name say-hello --dispatcher local --option callable=examples.hello:say_hello --payload '{"name":"World"}'

flowq worker --queue-backend file --file-queue-path ./.flowq/queue.jsonl --once
```

4) Configure SQS (prod-like). Set env and run:

```bash
export FLOWQ_QUEUE_BACKEND=sqs
export FLOWQ_SQS_QUEUE_URL=https://sqs.<region>.amazonaws.com/<acct>/<queue>
export AWS_REGION=<region>

flowq enqueue --name job --dispatcher lambda --option function_name=my-function --payload '{"x":1}'
flowq worker --once
```

Configuration
-------------

flowq loads settings from a YAML file (point `FLOWQ_CONFIG` to it) and/or environment variables. CLI flags override both.

Minimal example YAML:

```yaml
environment: dev
queue_backend: file
file_queue_path: ./.flowq/queue.jsonl
aws_region: us-east-1
sqs_queue_url: null
```

Dispatchers
-----------

- local: Calls a Python callable ("module:function") in-process.
- lambda: Invokes AWS Lambda.
- ecs: Runs an ECS task.
- sfn: Starts a Step Functions execution.

License
-------

MIT

