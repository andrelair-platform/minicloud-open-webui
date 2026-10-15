FROM ghcr.io/open-webui/open-webui:v0.11.3@sha256:41daa0cf2561a5d4c8d1ff31ee2a98d93ab4d3ac2605cac69366ff6a3374a933

USER root

RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

# CA cert injected at build time via --build-arg (CI passes MINICLOUD_CA_CERT secret).
# Never committed to the repo — internal infrastructure detail.
# Baked into a bundle alongside all system CAs (SSL_CERT_FILE points to /ca-bundle.crt).
ARG CA_CERT
RUN echo "${CA_CERT}" > /tmp/minicloud-ca.crt \
    && cat /etc/ssl/certs/ca-certificates.crt /tmp/minicloud-ca.crt > /ca-bundle.crt \
    && rm /tmp/minicloud-ca.crt

# Apply the French BM25 preprocessor to Open WebUI's retrieval layer at build time.
# Equivalent to the patch-bm25-french init container — identical patch logic,
# runs once during docker build instead of at every pod start.
# Patches /app/backend/open_webui/retrieval/utils.py in-place.
COPY patches/patch_bm25_french_build.py /tmp/patch_bm25_french_build.py
RUN python3 /tmp/patch_bm25_french_build.py \
    && grep -q '_french_bm25_preprocess' /app/backend/open_webui/retrieval/utils.py \
    && echo "BM25 French patch verified" \
    && rm /tmp/patch_bm25_french_build.py

# Add prometheus-fastapi-instrumentator so Prometheus can scrape /metrics from Open WebUI.
# sitecustomize.py is auto-loaded by Python before any user code — it patches
# FastAPI.__init__ so every FastAPI app (including Open WebUI) gets instrumented
# with http_request_duration_seconds histogram and http_requests_total counter.
COPY patches/sitecustomize.py /tmp/sitecustomize.py
RUN pip install "prometheus-fastapi-instrumentator>=7.1.0" --quiet \
    && python3 -c "import site, shutil; shutil.copy('/tmp/sitecustomize.py', site.getsitepackages()[0]+'/sitecustomize.py')" \
    && rm /tmp/sitecustomize.py
