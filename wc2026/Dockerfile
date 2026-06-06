# ── WC 2026 Dashboard — Dockerfile ─────────────────────────────────────────────
#
# Build:  docker build -t wc2026-dashboard .
# Run:    docker run -p 8501:8501 \
#           -e RAPIDAPI_KEY=your_key \
#           -e NEWSAPI_KEY=your_key \
#           wc2026-dashboard
# Open:   http://localhost:8501

FROM python:3.11-slim

# System dependencies (needed for some ML packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (Docker cache layer — only reinstalls if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for saved ML models
RUN mkdir -p models/saved

# ── Streamlit configuration ────────────────────────────────────────────────────
RUN mkdir -p /root/.streamlit
COPY .streamlit/config.toml /root/.streamlit/config.toml

# Expose Streamlit default port
EXPOSE 8501

# Health check — verifies the app is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Start command
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
