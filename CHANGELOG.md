# Changelog

## [0.1.1](https://github.com/andrelair-platform/minicloud-open-webui/compare/minicloud-open-webui-v0.1.0...minicloud-open-webui-v0.1.1) (2026-08-14)


### Features

* **catalog:** add argocd/app-name annotation ([8cf7785](https://github.com/andrelair-platform/minicloud-open-webui/commit/8cf7785b2a275c448ad4b187734ecb869152f536))
* **catalog:** add Backstage catalog-info.yaml ([29a6e42](https://github.com/andrelair-platform/minicloud-open-webui/commit/29a6e42e310564a4ba89b15ec3b7f5c897af43e2))
* initial custom Open WebUI image with baked-in CA cert and French BM25 patch ([95c6c49](https://github.com/andrelair-platform/minicloud-open-webui/commit/95c6c49b5fd9b2458a65b718bac33bc5acd0749b))
* **metrics:** add prometheus-fastapi-instrumentator for /metrics endpoint ([f877610](https://github.com/andrelair-platform/minicloud-open-webui/commit/f877610e3fbadd9465f1c408884ffe72381c2196))


### Bug Fixes

* **ci:** add OCI Accept header to Harbor pre-flight manifest check ([88af74f](https://github.com/andrelair-platform/minicloud-open-webui/commit/88af74f0567768ec3ef3ee9d74b8d06604c5a44c))
* **ci:** bump-gitops via PR instead of direct push to main ([32228c7](https://github.com/andrelair-platform/minicloud-open-webui/commit/32228c77c4123b88e0533c54673c7fa3fb15b1ae))
* **ci:** increase Trivy scan timeout to 15m for large images ([c6abf23](https://github.com/andrelair-platform/minicloud-open-webui/commit/c6abf235b04f91308451dfa4116fd00f4c35345e))
* **security:** upgrade base image packages to clear CRITICAL CVEs ([50d18c9](https://github.com/andrelair-platform/minicloud-open-webui/commit/50d18c931c058985cf9984960bba90286eb54ba5))

## Changelog

All notable changes to minicloud-open-webui are documented here.

This file is maintained by [release-please](https://github.com/googleapis/release-please).
