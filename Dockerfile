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

    # Collect static files
    RUN python manage.py collectstatic --noinput

    # Apply database migrations (crucial for production!)
    # Pass DATABASE_URL explicitly to the migrate command to ensure it connects to Supabase
    # The DATABASE_URL from Koyeb env vars needs to be available at this build step.
    # Using 'ARG' and 'ENV' in build or passing directly
    # A common way is to expose it as an ARG and then use ENV
    # However, for RUN commands, it's often best if the platform injects it.
    # Let's try passing it via the environment variables available during build.
    # This assumes Koyeb makes env vars available to RUN commands.

    # If the above doesn't work, we might need to define DATABASE_URL as a build-arg
    # ARG DATABASE_URL
    # ENV DATABASE_URL=$DATABASE_URL
    # RUN python manage.py migrate

    # But first, let's try assuming the DATABASE_URL is accessible from Koyeb's build environment
    # If not, the current method should fail.
    # The previous traceback tells us it's defaulting to SQLite, implying DATABASE_URL isn't set or valid.

    # To force it to use the production DB during build step:
    # You MUST ensure DATABASE_URL is correctly set in Koyeb's build-time environment variables.
    # Or, modify settings.py to crash if DATABASE_URL is not set (during DEBUG=False build)
    # to make the error clearer.

    # Let's add a check and make sure DATABASE_URL is actually used by migrate:
    # We will use the DJANGO_SETTINGS_MODULE to ensure settings.py is used correctly.
    # And ensure DATABASE_URL is set in Koyeb's environment for the build phase.

    # The simplest robust fix is often to explicitly pass the env var to the command:
    RUN DATABASE_URL=${DATABASE_URL} python manage.py migrate --noinput

    # Define the PORT environment variable
    ENV PORT=8000

    # Gunicorn start command
    CMD gunicorn study_platform.wsgi --bind 0.0.0.0:"${PORT}" --workers 2 --timeout 120
