FROM python:3.12-slim

# Install protobuf compiler
RUN apt-get update && \
    apt-get install -y protobuf-compiler && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Generate protobuf Python module
RUN protoc --python_out=./app/proto ./app/proto/track.proto

# Create __init__.py files for Python packages
RUN touch app/__init__.py app/services/__init__.py app/proto/__init__.py

# Expose TCP ports
EXPOSE 9001 9002 9003

# Run the application
CMD ["python", "-m", "app.main"]