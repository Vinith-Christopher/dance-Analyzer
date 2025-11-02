FROM python:3.12.0-slim

# Your existing RUN commands...

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/uploads /app/processed && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership of all files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]