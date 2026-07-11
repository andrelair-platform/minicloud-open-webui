## Summary

<!-- What does this PR change and why? 2-3 sentences. -->

## Type of change

- [ ] Open WebUI base image version bump
- [ ] BM25 French patch update
- [ ] CA certificate update
- [ ] CI / tooling
- [ ] Documentation

## Checklist

- [ ] Dockerfile builds locally with `docker build .`
- [ ] `grep -q '_french_bm25_preprocess' /app/backend/open_webui/retrieval/utils.py` passes in built image
- [ ] No secrets or credentials added to any file (minicloud-ca.crt is public — OK to commit)
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] If bumping base image: updated digest in `FROM` line

## If bumping the Open WebUI base image

- [ ] Verified `BM25Retriever.from_texts()` call signature unchanged in new version's utils.py
- [ ] Updated `FROM` digest: `crane digest ghcr.io/open-webui/open-webui:<new-tag>`
- [ ] Updated init container image references in minicloud-gitops open-webui-values.yaml (Phase A only)

## Related issues

<!-- Closes #<number> -->
