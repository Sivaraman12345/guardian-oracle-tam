# ──────────────────────────────────────────────────────────────
# Guardian Oracle TAM — Production Container
# ──────────────────────────────────────────────────────────────

FROM python:3.11-slim

LABEL maintainer="Guardian Oracle Team"
LABEL version="1.0"
LABEL description="Edge-AI smart trawling net — ecological stress detector & blockchain oracle"

# --- System dependencies ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends bash && \
    rm -rf /var/lib/apt/lists/*

# --- Working directory ---
WORKDIR /app

# --- Install Python dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy application code ---
COPY . .

# --- Create a non-root user ---
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# --- Healthcheck ---
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import edge_node.twis; print('OK')" || exit 1

# --- Default entrypoint ---
ENTRYPOINT ["python", "main.py"]
