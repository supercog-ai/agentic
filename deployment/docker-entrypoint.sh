#!/bin/bash
set -e

# Load environment variables from .env file if it exists
if [ -f /app/.env ]; then
  echo "Loading environment variables from .env file"
  export $(grep -v '^#' /app/.env | xargs)
fi

# Get agent path from environment variable or command line argument
AGENT_PATH=${AGENT_PATH:-$1}

if [ -z "$AGENT_PATH" ]; then
  echo "Error: AGENT_PATH environment variable or command line argument is required."
  echo "Usage: docker run -e AGENT_PATH=agents/your_agent.py ..."
  echo "   or: docker run ... agents/your_agent.py"
  exit 1
fi

# Check if the agent file exists
if [ ! -f "/app/$AGENT_PATH" ]; then
  echo "Error: Agent file '/app/$AGENT_PATH' not found."
  exit 1
fi

# Extract secrets from AWS Secrets Manager if available and AWS credentials are configured
if [ ! -z "$AWS_SECRET_NAME" ] && [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
  echo "Retrieving secrets from AWS Secrets Manager"
  
  # Install AWS CLI if not already installed
  if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI"
    pip install awscli
  fi
  
  # Get secrets from AWS Secrets Manager
  secrets=$(aws secretsmanager get-secret-value --secret-id $AWS_SECRET_NAME --query SecretString --output text)
  
  # Parse JSON and set environment variables
  echo $secrets | python -c "
import json, os, sys
secrets = json.loads(sys.stdin.read())
for key, value in secrets.items():
  os.system(f\"agentic secrets set {key} '{value}'\" if value else f\"agentic secrets set {key} ''\")"
fi

# Configure runtime directory
echo "Setting up runtime directory"
mkdir -p /app/runtime
agentic settings set AGENTIC_RUNTIME_DIR /app/runtime

# Start the appropriate service based on DEPLOYMENT_MODE
if [ "$DEPLOYMENT_MODE" = "dashboard" ]; then
  echo "Running pre-built dashboard for agent: $AGENT_PATH"
  exec agentic dashboard run --agent-path "$AGENT_PATH" --agent-port ${AGENT_PORT:-8086} --port ${DASHBOARD_PORT:-3000} $([ "$USE_RAY" = "true" ] && echo "--use-ray") $([ "$USER_AGENTS" = "true" ] && echo "--user-agents")
else
  echo "Starting the API server for agent: $AGENT_PATH"
  exec agentic serve "$AGENT_PATH" --port ${AGENT_PORT:-8086} $([ "$USE_RAY" = "true" ] && echo "--use-ray") $([ "$USER_AGENTS" = "true" ] && echo "--user-agents")
fi
