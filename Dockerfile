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

# --- New Debugging Step ---
# Verify gunicorn is installed and available in the PATH for the CMD command
# This step will fail the build if gunicorn is not found after installation
RUN /usr/local/bin/python -c "import gunicorn" || (echo "Gunicorn import failed, checking pip list..." && pip list && exit 1)
RUN which gunicorn || (echo "Gunicorn not found in PATH, trying common locations..." && ls -l /usr/local/bin/gunicorn /usr/bin/gunicorn /usr/local/pythons/bin/gunicorn && exit 1)
# --- End Debugging Step ---

# Copy the rest of the application code into the container
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Define the PORT environment variable
ENV PORT=8000

# Gunicorn start command (already robust, but double-check)
CMD ["/usr/local/bin/python", "-m", "gunicorn", "study_platform.wsgi", "--bind", "0.0.0.0:$(PORT)", "--workers", "2", "--timeout", "120"]
