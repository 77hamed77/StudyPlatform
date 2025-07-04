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
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# IMPORTANT: Make Supabase (S3) variables available during build time
# Define them as build arguments. These need to be passed during `docker build` or set in Koyeb/Render build settings.
ARG AWS_ACCESS_KEY_ID_BUILD
ARG AWS_SECRET_ACCESS_KEY_BUILD
ARG AWS_STORAGE_BUCKET_NAME_BUILD
ARG AWS_S3_ENDPOINT_URL_BUILD
ARG AWS_LOCATION_BUILD
ARG AWS_S3_REGION_NAME_BUILD

# Set them as environment variables for subsequent RUN commands (e.g., migrate)
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID_BUILD
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY_BUILD
ENV AWS_STORAGE_BUCKET_NAME=$AWS_STORAGE_BUCKET_NAME_BUILD
ENV AWS_S3_ENDPOINT_URL=$AWS_S3_ENDPOINT_URL_BUILD
ENV AWS_LOCATION=$AWS_LOCATION_BUILD
ENV AWS_S3_REGION_NAME=$AWS_S3_REGION_NAME_BUILD

# Collect static files
RUN python manage.py collectstatic --noinput

# Apply database migrations (crucial for production!)
# DATABASE_URL is expected to be available as an environment variable from Koyeb/Render
# or passed as a build argument if not directly available to RUN commands.
# Assuming it's available, as per previous discussions.
RUN python manage.py migrate --noinput

# Define the PORT environment variable
ENV PORT=8000

# Gunicorn start command
CMD gunicorn study_platform.wsgi --bind 0.0.0.0:"${PORT}" --workers 2 --timeout 120
