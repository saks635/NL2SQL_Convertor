FROM python:3.11-slim

WORKDIR /app

# Copy minimal requirements and install dependencies
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

# Copy simple application
COPY app_simple.py .

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Run the application
CMD ["python", "app_simple.py"]
