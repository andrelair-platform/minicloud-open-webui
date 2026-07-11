---
name: Bug report
about: Report a broken or unexpected behaviour
labels: bug
---

## Describe the bug

<!-- A clear description of what is broken. -->

## Steps to reproduce

1. '...'
2. See error: '...'

## Expected behaviour

<!-- What should have happened? -->

## Environment

| Field | Value |
|---|---|
| Image tag | <!-- from helm-values/open-webui-values.yaml in minicloud-gitops --> |
| Open WebUI base version | 0.9.4 |
| Component | <!-- OIDC / BM25 French / CA cert / RAG / SearXNG --> |
| Open WebUI pod status | <!-- kubectl get pods -n ai -l app.kubernetes.io/name=open-webui --> |

## Logs

<!-- kubectl logs -n ai -l app.kubernetes.io/name=open-webui --tail=50 -->
