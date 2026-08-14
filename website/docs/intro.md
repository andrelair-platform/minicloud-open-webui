---
id: intro
title: Overview
sidebar_label: Overview
slug: /
---

# minicloud Open WebUI

Custom **Open WebUI** container image for the minicloud enterprise AI platform — minicloud CA certificate baked in for internal TLS trust, and French BM25 tokenisation patch applied for RAG quality on French insurance documents.

## Responsibility

| In scope | Out of scope |
|---|---|
| CA cert injection (`minicloud-ca.crt`) | LiteLLM routing config (minicloud-gitops) |
| French BM25 patch (BM25 tokeniser for French) | Model deployment (vLLM, Ollama) |
| Custom entrypoint hardening | RAG pipeline (rag-ingest service) |

## Stack

| Concern | Choice |
|---|---|
| Base image | `ghcr.io/open-webui/open-webui:latest` |
| Language | Python 3.11 |
| AI gateway | LiteLLM (`litellm.devandre.sbs`) |
| RAG | pgvector (Qdrant-compatible API) |
| Registry | `harbor.10.0.0.200.nip.io/library/open-webui` |

## Customisations

| Patch | Why |
|---|---|
| `minicloud-ca.crt` added to system trust | Trusts internal Harbor, Vault, Langfuse, LiteLLM TLS without certificate errors |
| French BM25 tokeniser | Default English BM25 splits French words incorrectly, degrading keyword search recall on insurance docs |

## Links

- [GitHub repository](https://github.com/andrelair-platform/minicloud-open-webui)
- [Live instance](https://chat.devandre.sbs)
- [Platform documentation](https://andrelair-platform.github.io/minicloud-platform-docs/)
