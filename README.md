# K-Query

[![CI](https://github.com/maruthisai25/K_Query/actions/workflows/ci.yml/badge.svg)](https://github.com/maruthisai25/K_Query/actions/workflows/ci.yml)

A Slack bot that answers Kubernetes and monitoring questions by pulling live cluster state and
metrics into the prompt of a locally hosted model. You type `/devops why are my pods crashing?`
in Slack; it reads the pods in its namespace, searches a small document set for relevant text,
and asks Ollama to put the two together.

Everything runs inside your own infrastructure. No cluster state, metric, or question leaves the
network, which is the reason for using Ollama rather than a hosted API.

## What a request actually does

`POST /chat` handles one message at a time. It always searches the vector store, then decides
whether to gather anything else by looking for substrings in the message:

| If the message contains | It calls |
| --- | --- |
| `pod`, `deployment`, `service`, `namespace`, `kubectl` | the Kubernetes API |
| `metrics`, `cpu`, `memory`, `error`, `latency` | Prometheus |

That is substring matching, not intent classification (`src/main.py`). It is crude, but it is also
predictable, and for something that reads from a production cluster I would rather have a routing
rule I can read off the page than one I have to debug.

The Kubernetes reads go through the official `kubernetes` Python client, not `kubectl`. There is
no `kubectl` binary in the image. Each call is a `list_namespaced_*` against the single namespace
in `KUBERNETES_NAMESPACE`, truncated to the first 5 objects (3 for events) so the prompt stays
small. The RBAC in `k8s/rbac.yaml` grants `get`, `list` and `watch` and nothing else, so the bot
cannot change anything in the cluster.

Prometheus access is four fixed PromQL queries in `src/prometheus_client.py`, one each for CPU,
memory, error rate and p95 latency. The model does not write PromQL.

## Running it

```bash
git clone https://github.com/maruthisai25/K_Query.git
cd K_Query
cp .env.example .env    # add your Slack bot token and signing secret
docker compose up -d
```

That brings up five containers: the app on 8000, Ollama on 11434, Qdrant on 6333, Prometheus on
9090 and Grafana on 3000.

On first startup the app creates the `devops_knowledge` collection in Qdrant and seeds it. You do
not need to run anything else for that; `scripts/setup.sh` does the same thing if you want to seed
without starting the app.

The model is not bundled. The first `/chat` request triggers a pull of `llama2:7b`, which is about
3.8 GB and will take a while. Pulling it up front is less surprising:

```bash
docker compose exec ollama ollama pull llama2:7b
```

Check it came up:

```bash
curl -s localhost:8000/health | jq
curl -s localhost:8000/livez
```

`/health` reports on all four dependencies and returns 503 if any is down. `/livez` only reports
whether the process is serving; that is the one wired to the Kubernetes liveness probe, so a
Prometheus blip does not restart the app.

### Without Docker

Python 3.11 or newer. Qdrant and Ollama need to be reachable.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export SLACK_BOT_TOKEN=xoxb-... SLACK_SIGNING_SECRET=...
python -m src.main
```

`pip install` pulls torch through sentence-transformers, so the first install is a few hundred
megabytes and several minutes.

### Slack setup

Create an app at [api.slack.com/apps](https://api.slack.com/apps) with the `app_mentions:read`,
`chat:write`, `commands`, `im:read` and `im:write` scopes, add a `/devops` slash command pointing
at `https://your-host/slack/events`, install it, and copy the bot token and signing secret into
`.env`. Direct messages to the bot work the same way as the slash command.

## Kubernetes

```bash
kubectl apply -k k8s/
```

This needs the prometheus-operator `ServiceMonitor` and `PrometheusRule` CRDs to already exist,
otherwise the apply fails on those two resources. CI installs them from the operator repo before
applying; see `.github/workflows/ci.yml` if you want the exact URLs.

What gets created: the app as a 2-replica Deployment behind a LoadBalancer, Ollama and Qdrant as
single-replica Deployments with their own ClusterIP Services and PVCs, an HPA scaling the app from
2 to 10, NetworkPolicies, RBAC, and the ServiceMonitor and alert rules.

Ollama runs as its own Deployment rather than inside the app image. Baking it in meant copying
`/bin/ollama` without `/usr/lib/ollama`, so the server started, `/api/tags` returned 200, every
health check passed, and generation failed with `llama-server binary not found`. Splitting it out
avoids that entirely and lets the app scale past one replica while the model cache stays on a
single ReadWriteOnce volume.

Secrets are placeholders in `k8s/kustomization.yaml`. Replace them before applying anywhere real.

One known bad manifest: `k8s/prometheus-adapter.yaml` passes `--logtostderr=true`, which
prometheus-adapter v0.11.0 rejects with `unknown flag: --logtostderr`, so that Deployment
crash-loops. It only feeds the custom metric the HPA uses as its third signal; CPU and memory
scaling work without it.

Images for `linux/amd64` and `linux/arm64` are built and pushed to
`ghcr.io/maruthisai25/k-query` by `.github/workflows/publish.yml` on pushes to `main` and on
version tags.

## Retries and the circuit breaker

Calls to Ollama are wrapped in a retry decorator and a circuit breaker (`src/resilience.py`).
Three attempts with exponential backoff; a request that fails all three counts as one failure
against the breaker, and three such failures open it for 30 seconds, during which `/chat` returns
503 immediately without touching the network.

The ordering matters and it was wrong for a while. With retries on the outside, one bad request
recorded three failures and tripped a threshold of three by itself, taking Ollama out for 30
seconds after a single blip.

## Metrics

`/metrics` exposes:

```
http_requests_total{endpoint,method,status}
http_request_duration_seconds{endpoint,method}
chat_requests_total
chat_request_duration_seconds
```

`endpoint` is the matched route template rather than the raw path, so `/chat` stays one series.
The alert rules in `k8s/servicemonitor.yaml` cover request rate, 5xx ratio and p95 latency.

## Layout

```
src/main.py              FastAPI app, routing, metrics middleware
src/slack_bot.py         slash command and DM handlers
src/llm_service.py       Ollama client
src/vector_store.py      Qdrant client and the embedding model
src/k8s_client.py        Kubernetes reads
src/prometheus_client.py the four PromQL queries
src/resilience.py        retry decorator and circuit breaker
src/config.py            environment configuration and validation
k8s/                     manifests, applied with kustomize
scripts/setup.sh         seeds Qdrant without starting the app
```

Embeddings come from `sentence-transformers/all-MiniLM-L6-v2`: 384 dimensions, cosine distance.
Searching the seeded corpus for "why is my pod in CrashLoopBackOff?", a phrasing that appears in
none of the three documents, returns:

```
score=0.6754  source=kubernetes-troubleshooting.md
score=0.4632  source=performance-troubleshooting.md
```

If the vector search raises, `search()` falls back to scrolling the collection and matching
keywords, which is worse but returns something.

## What is not built

This is the part worth reading before you judge the rest.

The biggest gap is the corpus. It is three documents, hardcoded in `_populate_initial_faqs` in
`src/vector_store.py`, covering pod troubleshooting, CPU troubleshooting and deployment
troubleshooting. `add_document()` exists and works, but nothing calls it with a file, a directory
or a URL, so there is no ingestion path, no chunking and no re-indexing. Calling this "runbook
search" would be a lie; it is three paragraphs and a nearest-neighbour lookup. Pointing it at a
real runbook repository is the one change that would make the retrieval half of this worth
anything, and it is not done.

Seeding is also not idempotent in the direction you would want. `initialize_collection()` returns
early when the collection already exists, so an existing but empty collection never gets seeded.
`setup.sh` detects that case and tells you to drop the collection rather than repairing it.

There is no authentication. `/chat` will answer anything that can reach the pod. Slack requests to
`/slack/events` are signature-verified by slack-bolt, but the chat endpoint has no auth, no rate
limiting and no per-user quota. The NetworkPolicy is the only thing keeping it reachable from
inside the cluster alone, and a NetworkPolicy is not an authorization system.

State is per-process. The circuit breaker is a module-level global, so with `replicas: 2` each pod
has its own and "the breaker is open" can be true for one pod and false for the other. Nothing is
shared, and there is no conversation memory: each message is answered on its own, and a follow-up
question does not know what you asked before it.

What it can see is narrow. One namespace, the first five objects of each kind, three events, no
logs, nothing cluster-wide, no `describe` output. On the metrics side it is four fixed queries, so
any question that is not about CPU, memory, error rate or p95 latency reaches the model with no
data behind it.

Two smaller things. The model pull in `src/llm_service.py` uses a 300 second timeout, which a
3.8 GB download on a slow link will blow through, so pull out of band. And NetworkPolicy
enforcement is untested: CI applies the manifests to a kind cluster and a real API server accepts
them, but kind's default CNI does not implement NetworkPolicy, so what CI proves is that they are
valid, not that they block anything. Calico or Cilium would give the egress rules their first real
exercise.

Tests cover the clients, config validation, and the retry and breaker behaviour. Nothing exercises
the FastAPI endpoints, and nothing runs against a live Ollama.

## Development

```bash
make test      # pytest with coverage
make lint      # black, isort, flake8
make build     # docker build
make deploy    # kubectl apply -k k8s/
make status    # health of the compose stack
```

CI runs lint, the test suite, `kubectl kustomize k8s/` with an assertion that every Deployment and
Service kept its own selector, an apply against a kind cluster, and a Docker build.

Current state locally:

```
$ pytest -q
..........                                                               [100%]
10 passed
```

## License

MIT. See [LICENSE](LICENSE).
