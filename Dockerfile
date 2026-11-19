# Base image: Official Python 3.12 slim image for minimal footprint and reproducible execution
FROM python:3.12-slim

# Set environment variables for Python in containerized environments
# - PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# - PYTHONUNBUFFERED: Forces stdin, stdout, and stderr to be unbuffered for immediate console streaming
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set standard working directory inside container
WORKDIR /app

# Install dependencies in a separate layer for optimal caching
COPY app/requirements.txt /app/app/requirements.txt
RUN pip install --no-cache-dir -r /app/app/requirements.txt

# Copy application source code
COPY app/ /app/app/

# Create a non-root system user for security best practices
RUN useradd -m -u 1000 gmtuser && chown -R gmtuser:gmtuser /app
USER gmtuser

# Keep container running in idle standby so GMT ScenarioRunner can attach
# metric providers during the BOOT phase and execute flow commands in RUNTIME.
CMD ["tail", "-f", "/dev/null"]
