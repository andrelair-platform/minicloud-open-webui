FROM ghcr.io/open-webui/open-webui:0.9.4@sha256:172e1fe0e89af2a07f42f2b1d943f30c8ddd7b9c2e182f3678b4790cdb83abea

USER root

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
