# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies required for building Python packages
# (e.g. gcc for some C-extensions, though many use wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment to isolate dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir six && \
    pip install --no-cache-dir --no-build-isolation hangulize==0.0.9 && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime system dependencies if necessary (e.g. libpq for postgres, but clean apt cache)
# Currently basic slim is often enough, but keeping update is good practice for security
RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN addgroup --system --gid 1001 python && \
    adduser --system --uid 1001 python

# Copy the virtual environment from the builder stage
COPY --from=builder --chown=python:python /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy application code
COPY --chown=python:python . .

# Switch to the non-root user
USER python

# Expose the port
EXPOSE 8000

# Run the application (Removed --reload for production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
