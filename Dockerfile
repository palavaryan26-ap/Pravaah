FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .

# Install the package and dependencies
# We install in a way that allows us to run it directly
RUN pip install --no-cache-dir -e .[ai]

# Copy the application code
COPY pravaah/ ./pravaah/
COPY config/ ./config/

# Create a directory for the database volume
RUN mkdir -p /app/data

# Default port
EXPOSE 8000

# Run the Pravaah CLI by default
CMD ["pravaah", "run", "--host", "0.0.0.0", "--port", "8000"]
