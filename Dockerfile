# Use a smaller base image
FROM python:3.12-slim

# Set environment variables for Python to not write pyc files and to buffer stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore::UserWarning

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        libgl1-mesa-dev \
        libglib2.0-0 \
        git \
        gettext \
        pkg-config \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install fonts via apt (no TTF downloads needed — fonts are versioned Debian packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        fonts-liberation \
        fonts-noto-core \
        fonts-freefont-ttf \
        fonts-lato && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install pip and pin setuptools to avoid pkg_resources deprecation warnings
RUN pip install --upgrade pip && \
    pip install "setuptools<81" wheel

# Install gunicorn, uvicorn
RUN pip install gunicorn uvicorn --no-cache-dir

# Create a non-root user with no password
RUN adduser app --disabled-password --no-create-home

# Create the app directory
WORKDIR /app

# Copy requirements.txt to the app directory
COPY requirements.txt /app/

# Install Python dependencies using pip (including psycopg2-binary)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project to the app directory
COPY . /app/

# Change work directory owner
RUN chown -R app:app /app \
    && chown -R app:app /app/* \
    && chmod +x /app/scripts/*

# Expose port 8000
EXPOSE 8000