# Use an official Python base image
# Use python:3.11-slim-buster to reduce image size
FROM python:3.11-slim-buster

# Update package lists and install essential build dependencies
# libpq-dev is necessary for psycopg2-binary if a pre-built wheel is not available
# build-essential, pkg-config, and git are common build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        pkg-config \
        git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Install Python dependencies
# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
# Use --default-timeout to increase download timeout
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Collect static files
# --noinput to avoid interactive prompts
RUN python manage.py collectstatic --noinput

# Define the PORT environment variable that the application will receive from the environment
# Koyeb will provide it automatically
ENV PORT=8000

# Gunicorn start command
# Uses the PORT variable provided by Koyeb
CMD ["gunicorn", "study_platform.wsgi", "--bind", "0.0.0.0:$(PORT)", "--workers", "2", "--timeout", "120"]
