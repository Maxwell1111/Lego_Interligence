# AI-Powered LEGO Architect - Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY lego_architect/ ./lego_architect/
COPY tests/ ./tests/
COPY *.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create directory for builds
RUN mkdir -p /builds

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command - run demo
CMD ["python", "demo.py"]
