# Use an official Python base image with a newer Debian version (e.g., bookworm for Debian 12)
FROM python:3.11-slim-bookworm

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
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# IMPORTANT: Make all variables available during build time
ARG AWS_ACCESS_KEY_ID_BUILD
ARG AWS_SECRET_ACCESS_KEY_BUILD
ARG AWS_STORAGE_BUCKET_NAME_BUILD
ARG AWS_S3_ENDPOINT_URL_BUILD
ARG AWS_LOCATION_BUILD
ARG AWS_S3_REGION_NAME_BUILD
ARG DATABASE_URL_BUILD
ARG DJANGO_SECRET_KEY_BUILD
ARG DJANGO_DEBUG_BUILD

# Set them as environment variables for subsequent RUN commands
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID_BUILD
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY_BUILD
ENV AWS_STORAGE_BUCKET_NAME=$AWS_STORAGE_BUCKET_NAME_BUILD
ENV AWS_S3_ENDPOINT_URL=$AWS_S3_ENDPOINT_URL_BUILD
ENV AWS_LOCATION=$AWS_LOCATION_BUILD
ENV AWS_S3_REGION_NAME=$AWS_S3_REGION_NAME_BUILD
ENV DATABASE_URL=$DATABASE_URL_BUILD
ENV DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY_BUILD
ENV DJANGO_DEBUG=$DJANGO_DEBUG_BUILD

# Collect static files
RUN python manage.py collectstatic --noinput

# Apply database migrations (crucial for production!)
# RUN python manage.py migrate --noinput

# Define the PORT environment variable
ENV PORT=8000

# Gunicorn start command
CMD python manage.py migrate --noinput && gunicorn study_platform.wsgi --bind 0.0.0.0:"${PORT}" --workers 2 --timeout 120
