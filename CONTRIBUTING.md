# Contributing

## Branch strategy

| Branch | Protection | CI output | GitOps update |
|---|---|---|---|
| `main` | PR required + GPG-signed commits | `<sha>-amd64` — cosign-signed | bumps `helm-values/open-webui-values.yaml` image tag |
| `staging` | PR required | `staging-<sha>-amd64` — cosign-signed | none |
| `dev` | open push | `dev-<sha>-amd64` | none |

## Commit style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add custom Langfuse prompt injection at startup
fix: update BM25 patch anchor for Open WebUI 0.10.x
chore: bump base image to open-webui:0.10.0
ci: pin cosign installer to v3.5
```

## Dev workflow

```bash
# Build the image locally
docker build -t open-webui-custom:local .

# Verify the BM25 patch was applied
docker run --rm open-webui-custom:local \
  grep -q '_french_bm25_preprocess' /app/backend/open_webui/retrieval/utils.py \
  && echo "BM25 patch OK"

# Verify the CA bundle was created
docker run --rm open-webui-custom:local \
  test -f /ca-bundle.crt && echo "CA bundle OK"
```

## Bumping the Open WebUI base image

1. Get the new digest: `crane digest ghcr.io/open-webui/open-webui:<new-tag>`
2. Update `FROM` in `Dockerfile` with new tag + digest
3. Verify the patch anchors still exist in the new version:
   ```bash
   docker run --rm ghcr.io/open-webui/open-webui:<new-tag> \
     grep 'BM25Retriever.from_texts' /app/backend/open_webui/retrieval/utils.py
   ```
4. If anchors changed, update `patches/patch_bm25_french_build.py` accordingly
5. Open a PR — CI will catch build failures before merge

## Phase B: removing init containers

Once the custom image is confirmed stable in production (Phase A), the init containers
and their ConfigMap can be removed from minicloud-gitops:

1. Delete `manifests/ai/09-bm25-french-patchscript.yaml`
2. In `helm-values/open-webui-values.yaml`:
   - Remove `extraInitContainers:` block
   - Remove `volumes:` entries: `minicloud-ca`, `ca-bundle`, `bm25-french-patchscript`, `patched-retrieval`
   - Remove `volumeMounts.container:` and `volumeMounts.initContainer:` blocks
   - Change `SSL_CERT_FILE` value from `/ca-bundle/bundle.crt` → `/ca-bundle.crt`
3. Commit, push → ArgoCD syncs → verify OIDC login + BM25 French + RAG still work

## Code standards

- Keep `Dockerfile` minimal — only the CA cert bake and BM25 patch
- `patches/patch_bm25_french_build.py` must exit 1 on any unexpected state — it is a safety gate
- No Co-Authored-By lines — commits represent the owner's portfolio work
