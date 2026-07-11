# minicloud-open-webui

[![CI](https://github.com/andrelair-platform/minicloud-open-webui/actions/workflows/ci.yml/badge.svg)](https://github.com/andrelair-platform/minicloud-open-webui/actions/workflows/ci.yml)
[![Supply chain: cosign](https://img.shields.io/badge/supply%20chain-cosign%20signed-green)](https://github.com/sigstore/cosign)

> Custom Open WebUI image for the minicloud enterprise AI platform. Extends the official Open WebUI image with two build-time customisations that eliminate init containers from the production deployment: the minicloud self-signed CA cert is baked into the system trust bundle, and the French BM25 preprocessor is patched into Open WebUI's retrieval layer at build time.

---

## Why a custom image?

The production deployment previously used **two init containers** as runtime workarounds:

| Init container | What it did | Status |
|---|---|---|
| `inject-minicloud-ca` | Concatenated minicloud CA + system CAs → `SSL_CERT_FILE` | Replaced by build-time CA bake |
| `patch-bm25-french` | Patched `open_webui/retrieval/utils.py` at pod start | Replaced by build-time patch |

Moving these into the Dockerfile means the init containers are no longer needed, pod startup is faster, and the customisations are versioned in source control with a proper CI pipeline.

---

## What this image adds

### 1. minicloud CA cert baked in

```dockerfile
COPY certs/minicloud-ca.crt /tmp/minicloud-ca.crt
RUN cat /etc/ssl/certs/ca-certificates.crt /tmp/minicloud-ca.crt > /ca-bundle.crt
```

Open WebUI calls the Authentik OIDC provider (`auth.devandre.sbs`) over HTTPS. The self-signed minicloud CA must be trusted for SSL verification to pass. The baked-in bundle lives at `/ca-bundle.crt`.

**Phase B:** `SSL_CERT_FILE=/ca-bundle.crt` in Helm values (replaces the init container output at `/ca-bundle/bundle.crt`).

### 2. French BM25 preprocessor baked in

```python
# patches/patch_bm25_french_build.py
# Patches /app/backend/open_webui/retrieval/utils.py
# Injects _french_bm25_preprocess() — NLTK Snowball French stemmer + stop-word filter
# Wires it into BM25Retriever.from_texts(preprocess_func=_french_bm25_preprocess)
```

Open WebUI's hybrid search runs `BM25Retriever` from LangChain alongside HNSW vector search. The default tokeniser is whitespace-only — "sinistres" and "sinistre" are different tokens. The French Snowball stemmer maps both to "sinistr", making BM25 useful for French insurance document retrieval.

**Verified:** `sinistres/sinistre → sinistr ✅`, `réassurance/réassurer → réassur ✅`

---

## Architecture

```
minicloud-open-webui (this repo)
    │
    │  docker build
    ▼
harbor.10.0.0.200.nip.io/library/open-webui:<sha>-amd64
    │
    │  ArgoCD detects new image tag in minicloud-gitops
    ▼
Open WebUI pod in ai namespace
    ├─ OIDC SSO → Authentik (auth.devandre.sbs) — CA in /ca-bundle.crt
    ├─ LiteLLM AI Gateway (8 providers) — http://litellm.ai.svc.cluster.local:4000
    ├─ pgvector RAG (hybrid BM25+HNSW) — PostgreSQL ragdb
    ├─ SearXNG web search — http://searxng.searxng.svc.cluster.local:8080
    └─ phi3-financial default model for finance analysts
```

---

## CI/CD pipeline

Every push to `main` triggers `.github/workflows/ci.yml`:

```
push to main
    │
    ├─ 1. Connect to Tailscale tailnet (reach Harbor registry directly over LAN)
    ├─ 2. Trust minicloud self-signed CA (Docker daemon + cosign + crane)
    ├─ 3. docker build → harbor.10.0.0.200.nip.io/library/open-webui:<sha>-amd64
    │       Dockerfile verifies BM25 patch applied: grep -q '_french_bm25_preprocess'
    ├─ 4. cosign sign (keyless — GitHub OIDC → Sigstore Fulcio)
    └─ 5. GPG-signed commit to minicloud-gitops
              bumps: helm-values/open-webui-values.yaml  image.tag: <sha>-amd64
                     ArgoCD webhook → rolling update in ai namespace
```

**Branch behaviour:**

| Branch | Image tag | Cosign signed | GitOps bump |
|---|---|---|---|
| `main` | `<sha>-amd64` | yes | yes — `helm-values/open-webui-values.yaml` |
| `staging` | `staging-<sha>-amd64` | yes | no |
| `dev` | `dev-<sha>-amd64` | no | no |

**Required secrets:**

| Secret | Purpose |
|---|---|
| `TS_OAUTH_CLIENT_ID` | Tailscale OAuth client ID (Settings → OAuth clients, tag:ci) |
| `TS_OAUTH_SECRET` | Tailscale OAuth client secret |
| `MINICLOUD_CA_CERT` | Self-signed CA PEM — lets Docker and cosign trust Harbor TLS |
| `HARBOR_USER` | Harbor registry username |
| `HARBOR_PASSWORD` | Harbor registry password |
| `GITOPS_TOKEN` | GitHub PAT (`repo` scope) for committing to `minicloud-gitops` |
| `GPG_PRIVATE_KEY` | Armored GPG private key for signing gitops commits (key `FD6D39D681DEFA34`) |

---

## Bumping the Open WebUI base image

```bash
# 1. Get new digest
crane digest ghcr.io/open-webui/open-webui:<new-tag>

# 2. Verify BM25 patch anchors are still present in the new version
docker run --rm ghcr.io/open-webui/open-webui:<new-tag> \
  grep 'BM25Retriever.from_texts' /app/backend/open_webui/retrieval/utils.py

# 3. Update FROM in Dockerfile with new tag + digest
# 4. Open PR — CI catches build failures before merge
```

---

## Migration status

| Phase | Description | Status |
|---|---|---|
| A | Custom image deployed; init containers still present (idempotent safety net) | ✅ Done |
| B | Remove init containers + ConfigMap; set `SSL_CERT_FILE=/ca-bundle.crt` | ✅ Done |

See `CONTRIBUTING.md` for Phase B instructions.

---

## Related services

| Service | Repo / Location | Role |
|---|---|---|
| **minicloud-gitops** | [andrelair-platform/minicloud-gitops](https://github.com/andrelair-platform/minicloud-gitops) | ArgoCD app + Helm values — `helm-values/open-webui-values.yaml` |
| **LiteLLM AI Gateway** | Helm in `ai` namespace | 8-provider LLM routing, PII guardrails, dept key governance |
| **minicloud-rag-ingest** | [andrelair-platform/minicloud-rag-ingest](https://github.com/andrelair-platform/minicloud-rag-ingest) | French insurance document ingestion → pgvector |
| **minicloud-markitdown-proxy** | [andrelair-platform/minicloud-markitdown-proxy](https://github.com/andrelair-platform/minicloud-markitdown-proxy) | Document conversion (PDF/images → Markdown) |
| **SearXNG** | Helm in `searxng` namespace | Self-hosted meta-search for real-time web search |
| **Authentik** | Helm in `authentik` namespace | OIDC SSO provider — 16 department groups |
