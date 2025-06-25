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

# IMPORTANT: Make DATABASE_URL available during build time for collectstatic and migrate
# Define it as a build argument
ARG DATABASE_URL_BUILD

# Set it as an environment variable for subsequent RUN commands
ENV DATABASE_URL=$DATABASE_URL_BUILD

# Collect static files
RUN python manage.py collectstatic --noinput

# Apply database migrations (crucial for production!)
# Now DATABASE_URL is available as an ENV var for this RUN command
RUN python manage.py migrate --noinput

# Define the PORT environment variable
ENV PORT=8000

# Gunicorn start command
CMD gunicorn study_platform.wsgi --bind 0.0.0.0:"${PORT}" --workers 2 --timeout 120
