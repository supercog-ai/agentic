# Agentic Framework AWS Deployment

This repository contains everything needed to deploy Agentic agents to AWS ECS using Docker and Terraform.

## Prerequisites

- [Python 3.12](https://www.python.org/downloads/) or newer
- [Docker](https://docs.docker.com/get-docker/) installed and running
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [Terraform](https://developer.hashicorp.com/terraform/downloads) installed (v1.0.0+)
- [AWS Account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) with appropriate permissions
- API keys for your LLMs ([OpenAI](https://platform.openai.com/api-keys), [Anthropic](https://console.anthropic.com/settings/keys), etc.)
- [uv](https://github.com/astral-sh/uv) for Python package management (recommended)

## Getting Started

### 1. Set Up Environment

```bash
mkdir -p ~/agentic
cd ~/agentic
uv venv --python 3.12
source .venv/bin/activate
```

### 2. Install Agentic Framework

```bash
pip install agentic-framework[all, deployment]
```

### 3. Initialize Project

```bash
agentic init
```

### 4. Build Your Agent

Create your agent in the `agents` directory. For example, `agents/my_agent.py`:

```python
from agentic.common import Agent, AgentRunner
from agentic.tools import WeatherTool

my_agent = Agent(
    name="Weather Agent",
    welcome="I can give you weather reports! Just tell me which city.",
    instructions="You are a helpful assistant specializing in weather information.",
    tools=[WeatherTool()],
    model="openai/gpt-4o-mini"
)

if __name__ == "__main__":
    AgentRunner(my_agent).repl_loop()
```

Test your agent locally:

```bash
python agents/my_agent.py
```

### 5. Configure Secrets

You have three options for configuring your secrets:

#### Option 1: Environment File (.env)
```bash
cp .env.example .env
# Edit .env to add your API keys
```

#### Option 2: AWS Secrets Manager (via Terraform)
Add your secrets to `terraform/terraform.tfvars` in the `secrets_values` map.

### 6. Configure Terraform

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform/terraform.tfvars with your configuration
```

### 7. Deploy to AWS

```bash
# Navigate to terraform directory
cd terraform
terraform init
terraform apply

# Return to project root
cd ..

# Build and push Docker image
export AWS_REGION=$(aws configure get region)
export ECR_REPO_URL=$(cd terraform && terraform output -raw ecr_repository_url)
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URL}
docker build --platform linux/amd64 -t ${ECR_REPO_URL}:latest .
docker push ${ECR_REPO_URL}:latest
```

### 8. Test Your Deployment

```bash
# Get the API endpoint URL
export API_URL=$(cd terraform && terraform output -raw agent_endpoint)

# Test the discovery endpoint
curl "$API_URL/_discovery"

# Test your agent
curl -X POST "$API_URL/weather-agent/process" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the weather like in New York?"}'
```

## Understanding the Deployment

This deployment creates:

1. **VPC with Public/Private Subnets**: Network infrastructure for your agents
2. **ECR Repository**: Stores your Docker images
3. **ECS Cluster and Service**: Runs your containerized agents
4. **AWS Secrets Manager**: Securely stores API keys and credentials
5. **CloudWatch Logs**: Captures logs from your agents
6. **Load Balancer**: Provides a stable endpoint for your agent API

## Managing Secrets

Three options for secret management:

1. **Environment File (.env)**: Best for local development
   - Simple setup, less secure for production

2. **AWS Secrets Manager**: Best for production deployments
   - Centralized management, secure, automatic rotation capabilities

## Troubleshooting

### Container Fails to Start
Check CloudWatch Logs for detailed error messages

### API Not Accessible
Verify security group rules allow traffic to the container port (default: 8086)

### Authentication Issues
Verify your API keys are correctly configured in your chosen secrets management system

## Cleaning Up

To destroy all AWS resources created by Terraform:

```bash
cd ~/agentic/terraform
terraform destroy
```
