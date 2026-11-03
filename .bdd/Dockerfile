# Test-only image: the browser and driver come from the same Debian repository.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pip install --no-cache-dir pipenv && pipenv sync --system --dev
COPY service ./service
COPY wsgi.py ./
COPY features ./features
ENV CHROME_BINARY=/usr/bin/chromium CHROMEDRIVER=/usr/bin/chromedriver
