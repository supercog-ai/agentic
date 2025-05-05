FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AGENTIC_DEBUG=off
ENV PORT=8086
ENV AGENT_PATH="<your_agent_path>"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY ./agents /app/agents
COPY ./tools /app/tools
COPY ./.env /app/.env

# Install Python dependencies
RUN pip install --no-cache-dir "agentic-framework[all]"

# Expose the port the app runs on
EXPOSE 8086

# Set the entrypoint that handles environment variables
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set the entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]
