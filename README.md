# Research with Receipts

Research with Receipts is a web agent for the Vultr Agent Rush hackathon (Challenge 1, Blast Radius Zero). Ask a plain-English question that spans public US government data — "Which food companies with Salmonella recalls also hold federal contracts?" — and the agent writes Python, runs it in a fresh locked-down container, and returns a short report where every fact links to the government API call that produced it. The control plane is a FastAPI app meant to run on a Vultr Cloud Compute VM. Agent reasoning goes to Vultr Serverless Inference. Each task's code runs as a non-root, read-only container with no secrets, hard CPU/memory/time caps, and an allowlist egress proxy, and that container is destroyed when the task ends. Contract-sales, compliance, and newsroom users get an audit-ready answer with receipts from FDA, NHTSA, SEC EDGAR, USAspending, the Federal Register, Census geocoding, and the ECB data API.

## Architecture

```
Browser ──> web (FastAPI on a Vultr Cloud Compute VM) ── holds the LLM key
              │  plan / code / explain ──> Vultr Serverless Inference
              │     https://api.vultrinference.com/v1  (OpenAI-compatible chat)
              │  docker run --rm, one container per task
              ▼
          sandbox container ── internal-only network ──> egress-proxy ──> public-data hosts
```

The agent loop in `app/agent.py` is: question → model writes one script that uses the `pubdata` library → sandbox executes it → on a non-zero exit, stderr is fed back for up to three tries → the executed rows and receipt URLs go back to the model, which writes a cited markdown report. A policy violation or a timeout is a containment event: the task stops and the environment is already gone.

| Containment | How it is enforced |
|---|---|
| Process isolation | New container per task, user `runner` (uid 10001), `--cap-drop ALL`, `no-new-privileges`, read-only rootfs. Set `SANDBOX_RUNTIME=runsc` for gVisor. |
| Secret hygiene | `LLM_API_KEY` stays in the `web` service. The sandbox process gets a scrubbed environment (covered by `tests/test_agent.py`). |
| Resource limits | 256 MB RAM, 0.5 CPU, 64 pids, 45 s wall clock, 32 MB `/tmp`. |
| Lifecycle | `docker run --rm`. The local test runner deletes its temp directory after every task. |
| Egress | The sandbox network is `internal: true`. The only path out is the proxy, and both the proxy and `pubdata` allow the same public-data hosts. |

Allowlist: `api.fda.gov`, `api.nhtsa.gov`, `datahub.transportation.gov`, `efts.sec.gov`, `data.sec.gov`, `api.usaspending.gov`, `www.federalregister.gov`, `geocoding.geo.census.gov`, `data-api.ecb.europa.eu`.

## Quickstart

Docker Compose builds three services: the sandbox image, the egress proxy, and the web app. The web container talks to the host Docker socket so it can start a throwaway sandbox on the internal network `pra_sandbox_net`.

```bash
git clone https://github.com/calvindrover-rgb/research-with-receipts.git
cd research-with-receipts
cp .env.example .env
docker compose up --build
```

Open http://localhost:8000.

With `LLM_API_KEY` empty, the control plane uses a deterministic offline writer (`LLM_PROVIDER` falls through to the mock). The sandbox still executes that code, so the Salmonella question and the **Containment test** button both run without a model key. The containment button asks the agent to call `evil.example.com`. `pubdata` refuses that host before opening a socket, the task status is `contained`, and `docker ps` shows the task container is gone (`--rm`). A script that dials the same host with the standard library instead of `pubdata` is stopped by the proxy, which logs `DENY evil.example.com`.

To exercise the real model, put a Vultr Serverless Inference key in `.env` and start again:

```bash
docker compose up --build
```

## Vultr Serverless Inference

Chat calls are OpenAI-compatible `POST /chat/completions`. The base URL already points at Vultr. Set the key and pick a chat model:

```bash
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.vultrinference.com/v1
LLM_API_KEY=your_vultr_serverless_inference_key   # VULTR_INFERENCE_API_KEY is also accepted
LLM_MAX_TOKENS=8192                               # reasoning model: leave room for hidden reasoning
LLM_MODEL=deepseek-v4.1-flash
```

`deepseek-v4.1-flash` is the chat model in [Vultr's current quickstart](https://api.vultrinference.com/docs). List what the API is serving (no key required) and copy any chat id into `LLM_MODEL`:

```bash
curl https://api.vultrinference.com/v1/models
```

On 2026-11-03 that catalog's concrete DeepSeek id was `deepseek-v4.1-flash-1017`.

Create the key in the Vultr console under Serverless Inference. It is read from the environment of the `web` service only.

## Develop and test

Offline tests use the mock model and the in-process sandbox (`SANDBOX_MODE=local`). They do not call Vultr or the public data APIs. `pytest.ini` puts the repo root on `sys.path`, which current pytest needs when you pass the `tests` directory.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
LLM_PROVIDER=mock SANDBOX_MODE=local .venv/bin/uvicorn app.main:app --port 8000
.venv/bin/pytest -q tests
```

`LIVE=1 .venv/bin/pytest -q tests` adds one end-to-end question against FDA and USAspending. GitHub Actions (`.github/workflows/tests.yml`) runs the offline file only.

Local mode is for development. The containment story judges should see is `docker compose`, where the proxy and `--rm` container are real.

## Deploy on a Vultr VM

1. Create a Vultr Cloud Compute instance (Ubuntu 24.04, 2 vCPU / 4 GB is enough) from the Docker marketplace image.
2. Clone this repo, copy `.env.example` to `.env`, and set `LLM_API_KEY`.
3. `docker compose up -d --build`
4. Open port 8000, or put a reverse proxy in front of it. That URL is the public demo.

## License

MIT. Copyright (c) 2026 Make Me $1 Million. The full text is in [LICENSE](LICENSE).
