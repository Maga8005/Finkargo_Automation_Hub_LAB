FROM python:3.11-slim

# Install LibreOffice and system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render provides this via $PORT environment variable)
EXPOSE 8000

# Start the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
