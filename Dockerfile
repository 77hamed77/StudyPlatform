# Use an official Python base image
FROM python:3.11-slim-buster

# Update package lists and install essential build dependencies
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
COPY requirements.txt .

# Install Python dependencies
# Ensure pip is up-to-date within the container for better compatibility
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Apply database migrations (crucial for production!)
# This command will be run every time the image is built
RUN python manage.py migrate

# Define the PORT environment variable
ENV PORT=8000

# Gunicorn start command
# Use shell form for CMD to correctly interpret environment variables like PORT
CMD gunicorn study_platform.wsgi --bind 0.0.0.0:"${PORT}" --workers 2 --timeout 120
