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

# IMPORTANT: Make DATABASE_URL and Cloudinary variables available during build time
# Define them as build arguments
ARG DATABASE_URL_BUILD
ARG CLOUDINARY_CLOUD_NAME_BUILD
ARG CLOUDINARY_API_KEY_BUILD
ARG CLOUDINARY_API_SECRET_BUILD

# Set them as environment variables for subsequent RUN commands
ENV DATABASE_URL=$DATABASE_URL_BUILD
ENV CLOUDINARY_CLOUD_NAME=$CLOUDINARY_CLOUD_NAME_BUILD
ENV CLOUDINARY_API_KEY=$CLOUDINARY_API_KEY_BUILD
ENV CLOUDINARY_API_SECRET=$CLOUDINARY_API_SECRET_BUILD

# Collect static files
RUN python manage.py collectstatic --noinput

# Apply database migrations (crucial for production!)
RUN python manage.py migrate --noinput

# Define the PORT environment variable
ENV PORT=8000

# Gunicorn start command
CMD gunicorn study_platform.wsgi --bind 0.0.0.0:"${PORT}" --workers 2 --timeout 120
