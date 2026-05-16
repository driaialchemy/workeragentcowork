# ── Base image ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── Install dependencies (separate layer for cache efficiency) ─────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ─────────────────────────────────────────────────────────
COPY . .

# ── Entry point ────────────────────────────────────────────────────────────────
# Pass the research topic as the first argument to docker run, e.g.:
#   docker run --rm --env-file .env workeragentcowork "Claude Cowork and Claude Code cost optimization"
ENTRYPOINT ["python", "orchestrator.py"]
CMD ["--help"]
