# minicloud-open-webui

[![CI](https://github.com/andrelair-platform/minicloud-open-webui/actions/workflows/ci.yml/badge.svg)](https://github.com/andrelair-platform/minicloud-open-webui/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open WebUI](https://img.shields.io/badge/Open%20WebUI-0.9.4-orange)](https://github.com/open-webui/open-webui)
[![Supply chain: cosign](https://img.shields.io/badge/supply%20chain-cosign%20signed-green)](https://github.com/sigstore/cosign)

> Custom Open WebUI image for the minicloud enterprise AI platform. Extends the official `open-webui:0.9.4` image with two build-time customisations: the minicloud self-signed CA is baked into the system trust bundle, and the French BM25 preprocessor is patched into Open WebUI's retrieval layer. Both customisations replace runtime init containers, making the production pod faster to start and the changes versioned in source control with a full CI pipeline.

**Live demo:** [https://chat.devandre.sbs](https://chat.devandre.sbs)

---

## Table of Contents

- [Why a custom image?](#why-a-custom-image)
- [What this image adds](#what-this-image-adds)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [CI/CD Pipeline](#cicd-pipeline)
- [Bumping the base image](#bumping-the-base-image)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Why a custom image?

The production deployment previously used **two init containers** as runtime workarounds:

| Init container | What it did | Status |
|---|---|---|
| `inject-minicloud-ca` | Concatenated minicloud CA + system CAs → `SSL_CERT_FILE` at pod start | Replaced by build-time CA bake |
| `patch-bm25-french` | Patched `open_webui/retrieval/utils.py` at every pod start | Replaced by build-time Python script |

Moving these into the Dockerfile means the init containers are gone, pod startup is faster (~30s saved), and both customisations are versioned alongside the Dockerfile with a proper CI pipeline, Trivy scan, and Cosign signature.

---

## What this image adds

### 1. Security patching

```dockerfile
RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*
```

The upstream image ships with packages that have known CRITICAL CVEs. This layer upgrades all fixable packages at build time. Trivy enforces this — CI fails if any unfixed CRITICAL CVEs remain after the upgrade.

### 2. minicloud CA cert baked into the system trust bundle

```dockerfile
ARG CA_CERT
RUN echo "${CA_CERT}" > /tmp/minicloud-ca.crt \
    && cat /etc/ssl/certs/ca-certificates.crt /tmp/minicloud-ca.crt > /ca-bundle.crt \
    && rm /tmp/minicloud-ca.crt
```

Open WebUI calls the Authentik OIDC provider (`auth.devandre.sbs`) over HTTPS. The minicloud CA must be trusted for TLS verification to pass. The CA PEM is injected at build time via `--build-arg CA_CERT=...` (never committed to the repo). The combined bundle lives at `/ca-bundle.crt`; `SSL_CERT_FILE=/ca-bundle.crt` is set in the Helm values to point Python's `ssl` module at it.

### 3. French BM25 preprocessor patched in at build time

```dockerfile
COPY patches/patch_bm25_french_build.py /tmp/patch_bm25_french_build.py
RUN python3 /tmp/patch_bm25_french_build.py \
    && grep -q '_french_bm25_preprocess' /app/backend/open_webui/retrieval/utils.py \
    && echo "BM25 French patch verified" \
    && rm /tmp/patch_bm25_french_build.py
```

Open WebUI's hybrid search runs `BM25Retriever` (LangChain) alongside HNSW vector search. The default tokeniser is whitespace-only — `"sinistres"` and `"sinistre"` are different tokens. The patch injects a French Snowball stemmer + stop-word filter so both map to the same stem:

```
sinistres / sinistre  →  sinistr   ✅
réassurance / réassurer  →  réassur  ✅
```

The patch script (`patches/patch_bm25_french_build.py`) is idempotent — it checks for its own fingerprint before applying, and exits non-zero if the upstream anchor strings are missing (i.e. the base image changed the file). The `grep -q` after the script turns a silent no-op into a CI-visible build failure.

---

## Architecture

```
minicloud-open-webui (this repo)
    │
    │  docker build --build-arg CA_CERT=<pem>
    ▼
harbor.10.0.0.200.nip.io/library/open-webui:<sha>-amd64
    │
    │  CI bumps helm-values/open-webui-values.yaml in minicloud-gitops
    ▼
ArgoCD (open-webui app) → rolling update in ai namespace
    │
    ├─ OIDC SSO     → Authentik (auth.devandre.sbs)   — trusted via /ca-bundle.crt
    ├─ LLM routing  → LiteLLM AI Gateway               — http://litellm.ai.svc.cluster.local:4000
    ├─ RAG          → pgvector (ragdb)                  — hybrid BM25+HNSW search
    ├─ Web search   → SearXNG                           — http://searxng.searxng.svc.cluster.local
    └─ Doc ingest   → minicloud-rag-ingest / markitdown-proxy (ai namespace)
```

| Component | Detail |
|---|---|
| Base image | `ghcr.io/open-webui/open-webui:0.9.4` (pinned by digest) |
| Registry | `harbor.10.0.0.200.nip.io/library/open-webui` (internal, via Tailscale) |
| Namespace | `ai` |
| ArgoCD app | `open-webui` |
| GitOps values | `minicloud-gitops/helm-values/open-webui-values.yaml` |
| Auth | Authentik OIDC (`auth.devandre.sbs`) — 16 department groups |
| Default model | `phi3-financial` via LiteLLM (Groq llama-3.1-8b-instant, Ollama phi4-mini fallback) |

---

## Prerequisites

| Tool | Notes |
|---|---|
| Docker | Any recent version with BuildKit support |
| minicloud CA cert | Required for local builds — `~/minicloud-ca.crt` on the Mac dev machine |
| `crane` (optional) | For inspecting the upstream image digest before bumping the base image |

---

## Getting Started

### Build locally

```bash
git clone https://github.com/andrelair-platform/minicloud-open-webui.git
cd minicloud-open-webui

# Inject the minicloud CA at build time (never committed to the repo)
docker build \
  --build-arg CA_CERT="$(cat ~/minicloud-ca.crt)" \
  -t open-webui-custom:local .
```

The build output will include:
```
BM25 French patch verified
```
If that line is missing, the patch failed silently — check the Python script output above it.

### Verify the customisations

```bash
# BM25 French preprocessor is present
docker run --rm open-webui-custom:local \
  grep -q '_french_bm25_preprocess' /app/backend/open_webui/retrieval/utils.py \
  && echo "BM25 patch OK"

# CA bundle was created
docker run --rm open-webui-custom:local \
  test -f /ca-bundle.crt && echo "CA bundle OK"
```

---

## CI/CD Pipeline

Every push to `main` triggers `.github/workflows/ci.yml`:

```
push to main
    │
    ├─ 1. Connect to Tailscale (OAuth — TS_OAUTH_CLIENT_ID / TS_OAUTH_SECRET)
    ├─ 2. Trust minicloud CA on the runner (raw PEM — no base64 decode)
    ├─ 3. docker build → push to harbor.10.0.0.200.nip.io/library/open-webui:<sha>-amd64
    │       CA_CERT injected via --build-arg (MINICLOUD_CA_CERT secret)
    ├─ 4. Trivy scan — fails on unfixed CRITICAL CVEs (15 min timeout — large image)
    ├─ 5. cosign sign (keyless — GitHub OIDC → Sigstore Fulcio)
    ├─ 6. syft SBOM (CycloneDX JSON) — attached as OCI referrer
    └─ 7. GPG-signed commit to minicloud-gitops bumping helm-values/open-webui-values.yaml
              └─ ArgoCD webhook → rolling update in ai namespace
```

**Branch behaviour:**

| Branch | Image tag | Trivy | Cosign | SBOM | GitOps bump |
|---|---|---|---|---|---|
| `main` | `<sha>-amd64` | yes | yes | yes | `helm-values/open-webui-values.yaml` |
| `staging` | `staging-<sha>-amd64` | yes | yes | no | no |
| `dev` | `dev-<sha>-amd64` | yes | no | no | no |

### Required secrets

All 7 secrets are **org-level on `andrelair-platform`** (visibility: all). New repos inherit them automatically — no per-repo secret setup.

| Secret | Purpose |
|---|---|
| `TS_OAUTH_CLIENT_ID` | Tailscale OAuth client ID — joins tailnet as `tag:ci` |
| `TS_OAUTH_SECRET` | Tailscale OAuth secret |
| `MINICLOUD_CA_CERT` | Self-signed CA PEM — trusts Harbor TLS and baked into the image |
| `HARBOR_USER` | Harbor registry username |
| `HARBOR_PASSWORD` | Harbor registry password |
| `GITOPS_TOKEN` | GitHub PAT (`repo` scope) for committing to `minicloud-gitops` |
| `GPG_PRIVATE_KEY` | Armored GPG private key for signing gitops commits (key ID `FD6D39D681DEFA34`) |

### OCI image index (build-push-action v7)

`docker/build-push-action@v7` pushes an OCI image index (manifest list wrapping the image + provenance attestation). The Harbor pre-flight check passes the full OCI Accept header so the tag lookup returns 200:

```bash
-H "Accept: application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.docker.distribution.manifest.v2+json"
```

Without this header, Harbor returns 404 even when the tag exists.

---

## Bumping the base image

1. Find the new tag and digest:
   ```bash
   crane digest ghcr.io/open-webui/open-webui:<new-tag>
   ```

2. Verify the BM25 patch anchors still exist in the new version:
   ```bash
   docker run --rm ghcr.io/open-webui/open-webui:<new-tag> \
     grep -c 'BM25Retriever.from_texts' /app/backend/open_webui/retrieval/utils.py
   # must return 1

   docker run --rm ghcr.io/open-webui/open-webui:<new-tag> \
     grep -c 'from langchain_community.retrievers import BM25Retriever' /app/backend/open_webui/retrieval/utils.py
   # must return 1
   ```
   If either returns 0, update the anchor strings in `patches/patch_bm25_french_build.py` before bumping.

3. Update the `FROM` line in `Dockerfile` with the new tag and digest:
   ```dockerfile
   FROM ghcr.io/open-webui/open-webui:<new-tag>@sha256:<new-digest>
   ```

4. Open a PR against `main` — CI catches build or patch failures before merge.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| OIDC login fails with SSL error | `SSL_CERT_FILE` not set or pointing to wrong path | Verify `SSL_CERT_FILE=/ca-bundle.crt` is in `helm-values/open-webui-values.yaml` and the pod env: `kubectl exec -n ai <pod> -- env \| grep SSL_CERT` |
| BM25 search returns poor French results | BM25 patch not applied in the running image | Check build log for "BM25 French patch verified"; run verify command against the deployed image digest |
| CI fails: `patch anchor not found in utils.py` | Base image was bumped and Open WebUI changed the retrieval file | Update anchor strings in `patches/patch_bm25_french_build.py` — see [Bumping the base image](#bumping-the-base-image) |
| CI fails: CRITICAL CVEs from Trivy | Upstream image received new package CVEs | `apt-get upgrade` layer is already present — may need to bump the base image tag to get patched packages |
| CI fails: `context deadline exceeded` (Trivy) | Large image layers exceed Trivy's default scan timeout | `timeout: 15m` is already set on the Trivy step in `ci.yml` — verify it was not accidentally removed |
| Harbor pre-flight returns 404 after successful push | `build-push-action@v7` pushes an OCI image index; Harbor needs explicit Accept header | Accept header already set in `ci.yml` — re-check if the workflow was edited |
| Pod stuck after deploy | Open WebUI startup takes ~60s on first run (NLTK data download + model init) | Wait; check logs: `kubectl logs -n ai -l app.kubernetes.io/name=open-webui -f` |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch conventions, commit style, local verification commands, and the base image bump procedure.

---

## License

[MIT](LICENSE) © andrelair-platform
