# Selenium image used by the professor's Fall 2026 BDD workflow.
FROM quay.io/rofrano/pipeline-selenium:sp26

ENV CHROME_BINARY=/usr/bin/chromium CHROMEDRIVER=/usr/bin/chromedriver

ARG USERNAME=vscode
USER root

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
# The Selenium base already includes Pipenv; install only the locked packages.
RUN pipenv sync --system --dev

# Configuring insecure Docker registry
COPY config/insecure-registry.json /etc/docker/daemon.json 

# Become a regular user for development
USER $USERNAME

# Install user mode tools
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh
