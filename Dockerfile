# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Note: Sensitive environment variables should be passed at runtime, not baked into the image:
# - LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
# - OpenAI API keys, Deepgram API keys, and other AI service credentials

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY reqirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r reqirements.txt

# Copy project files into the container
COPY . .

# Create directory for logs if it doesn't exist
RUN mkdir -p /app/KMS/logs

# Expose port if needed (adjust as necessary)
# EXPOSE 8000

# Run the application
CMD ["python", "agent.py"]