# Product Brief — ktayl Knowledge Assistant

> **BMAD artefact:** Product Brief (Path **B** — lightweight, config-only, no custom backend).
> Board: **#18 ktayl Knowledge Assistant** (IS Foundations). Home: `minicloud-open-webui` + `minicloud-gitops`.
> Sister project: **ktayl-ai-copilot** (board #19) — the *beyond-OWUI* decision/action system.

## 1. What this is (one paragraph)

Turn the already-deployed **Open WebUI** into ktayl's **insurance knowledge assistant**: staff ask
questions about **policy wordings, underwriting guidelines, claims procedures, HR handbook, and
regulatory texts** and get **grounded, cited** answers. This is **config + content, not code** — Open
WebUI already does document RAG with citations + BM25; we simply feed it ktayl's curated corpora as
knowledge collections. Building a custom backend for this would be duplication.

## 2. Why this is a separate, *deliberately small* project

It is the honest answer to "if Open WebUI already covers it, don't rebuild it." Everything **OWUI can
do** (chat-over-docs, cited RAG) lives **here**. Everything OWUI **cannot** do (structured decisions,
authorized actions, multi-agent workflows) lives in the sister product **ktayl-ai-copilot (#19)**. The
two projects together are the clean split.

## 3. The problem

Underwriters, claims handlers and staff waste time hunting through wordings/guidelines/procedures and
sometimes rely on stale or wrong versions. A grounded, cited, always-current Q&A assistant over the
authoritative ktayl corpora fixes that — with **zero new application to build or secure** (read-only,
no actions → no authz boundary needed).

## 4. Scope

**In:** curate the authoritative ktayl document corpora (wordings, UW guidelines, claims procedures,
HR handbook, regulatory) → ingest via the existing **rag-ingest** pipeline → **OWUI knowledge
collections** (per-domain), with citations + BM25 hybrid search; access via existing **Authentik SSO**;
a small validation Q&A set to confirm grounding/citation quality; a refresh process for doc updates.

**Out:** any structured decision, any action into ktayl systems, any multi-agent flow, any custom
backend — all of that is **#19 ktayl-ai-copilot**. Also out: anything touching **Retrieva**.

## 5. Success metrics

Staff can get a cited, correct answer for the top-N insurance knowledge questions; citations point to
the authoritative current version; corpora stay fresh (defined refresh cadence); **no custom code
shipped** (the whole point).

## 6. Approach & deliverables (config, not build)

1. Corpus curation (which docs, which are authoritative, per-LOB grouping).
2. `rag-ingest` config + OWUI knowledge collections (per domain: underwriting / claims / policy / HR / regulatory).
3. OWUI model/prompt presets tuned for grounded, cited, refusal-on-insufficient answers.
4. SSO/access confirmation (staff groups via Authentik).
5. A validation Q&A set + a doc-refresh runbook.

All artefacts are **gitops/OWUI config** (`minicloud-gitops` helm-values + rag-ingest) — no new service.

## 7. Delivery path & gates

**Path B.** No architecture governance gate (no new architecture, no security boundary — read-only,
reuses OWUI+SSO+RAG). Stories on board **#18**; standard PR + CODEOWNERS for the gitops config.

## 8. Relationship to ktayl-ai-copilot (#19)

Knowledge Assistant = **"what does our guideline say?"** (OWUI, here). Copilot = **"assess THIS
submission → structured decision → act"** (beyond OWUI, #19). The copilot may *link out to* OWUI for
knowledge lookups, but its decisions/actions/authz never live in OWUI. Clean boundary, no overlap.
