# Agentic AWS Deployment Guide

This guide provides step-by-step instructions for deploying your Agentic agents to AWS using Docker and Terraform. 

> **Note:** If you have already completed the [Getting Started](../getting-started.md) guide, you can skip to [Step 5](#step-5-configure-secrets).

## Prerequisites

Before you begin, make sure you have the following:

- [Python 3.12](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/get-docker/) installed and running
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [Terraform](https://developer.hashicorp.com/terraform/downloads) installed (v1.0.0+)
- [AWS Account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) with appropriate permissions
- API keys for your LLMs ([OpenAI](https://platform.openai.com/api-keys), [Anthropic](https://console.anthropic.com/settings/keys), etc.)
- [uv](https://github.com/astral-sh/uv) for Python package management

## Step 1: Set Up Local Environment

Create a new directory for your project and navigate to it:

```bash
mkdir -p ~/agentic
cd ~/agentic
uv venv --python 3.12
source .venv/bin/activate
```

## Step 2: Install Agentic Framework

Next, install the Agentic framework with all optional dependencies:

```bash
pip install agentic-framework[all, deployment]
```

## Step 3: Initialize Your Project

Initialize a new Agentic project:

```bash
agentic init
```

This will create the basic project structure with example agents and tools.

## Step 4: Build Your Agent

Create or modify an agent in the `agents` directory. For example, `agents/my_agent.py`:

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

## Step 5: Configure Secrets

You have three options for configuring your secrets:

### Option 1: Environment File (.env)

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` to add your API keys and other secrets:

```
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
# Add other secrets as needed
```

When you build the docker image, the secrets will be automatically loaded into the container.

### Option 2: AWS Secrets Manager (via Terraform)

Secrets will be automatically configured in AWS Secrets Manager when you deploy using Terraform. You'll need to add your API keys to the `terraform/terraform.tfvars` file in step 6.

This approach is recommended for production deployments as it provides better security and centralized management.

## Step 6: Configure Terraform

1. Copy the example Terraform variables file:

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

2. Edit `terraform/terraform.tfvars` to configure your deployment:

```hcl
# AWS Region
aws_region = "us-east-1"

# Network Settings
vpc_name            = "agentic-vpc"
vpc_cidr            = "10.0.0.0/16"
availability_zones  = ["us-east-1a", "us-east-1b"]
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnet_cidrs = ["10.0.101.0/24", "10.0.102.0/24"]

# ECR Settings
ecr_repository_name = "agentic-api"

# ECS Settings
ecs_cluster_name      = "agentic-cluster"
task_cpu              = "1024"  # 1 vCPU
task_memory           = "2048"  # 2 GB
service_desired_count = 1

# Agent Settings
agent_path  = "agents/basic_agent.py"  # Path to your agent file
user_agents = false  # Set to true if you want to enable user-specific agents
use_ray     = false  # Set to true if you want to use Ray for agent execution

# Secrets Settings
secrets_name = "agentic-api-secrets"

# Replace these with your actual API keys in a secure way - DO NOT commit this file with real values
secrets_values = {
  OPENAI_API_KEY    = "your-openai-api-key"
  ANTHROPIC_API_KEY = "your-anthropic-api-key"
}
```

## Step 7: Build the Terraform Configuration

Navigate to the terraform directory and initialize Terraform:

```bash
cd terraform
terraform init
```

Review the infrastructure plan:

```bash
terraform plan
```

Apply the configuration to create the AWS resources:

```bash
terraform apply
```

You'll need to confirm the changes by typing `yes` when prompted.

## Step 8: Build and Deploy the Docker Image

Return to the project root directory and log in to your ECR repository:

```bash
cd ..  # Return to the project root from the terraform directory
export AWS_REGION=$(aws configure get region)
export ECR_REPO_URL=$(cd terraform && terraform output -raw ecr_repository_url)
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URL}
```

Build and push the Docker image:

```bash
docker build --platform linux/amd64 -t ${ECR_REPO_URL}:latest .
docker push ${ECR_REPO_URL}:latest
```

## Step 9: Test Your Deployment

Test your agent API by sending a request to the endpoint:

```bash
# Get the API endpoint URL from Terraform output
export API_URL=$(cd terraform && terraform output -raw agent_endpoint)

# Send a test request to the discovery endpoint
curl "$API_URL/_discovery"
```

You should see a list of available agent endpoints.

To test your agent, send a request to the process endpoint:

```bash
curl -X POST "$API_URL/weather-agent/process" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the weather like in New York?"}'
```

This will return a request ID, which you can use to get the events:

```bash
curl "$API_URL/weather-agent/getevents?request_id=YOUR_REQUEST_ID"
```

## Step 10: Monitor Your Deployment

You can monitor your agent in the AWS Console:

1. **ECS**: Check the status of your agent service
2. **CloudWatch**: View logs from your agent
3. **ECR**: Manage your Docker images

## Troubleshooting

### Container Fails to Start

Check CloudWatch Logs for detailed error messages:

1. Go to the AWS Console
2. Navigate to CloudWatch > Log Groups
3. Find the log group for your agent (usually `/ecs/your-agent-name`)
4. Check the latest log stream for error messages

### API Not Accessible

Verify security group rules allow traffic to the container port:

1. Go to the AWS Console
2. Navigate to EC2 > Security Groups
3. Find the security group associated with your agent
4. Ensure it allows inbound traffic on the container port (default: 8086)

### Authentication Issues

Ensure your API keys are correctly set up:

1. **For AWS Secrets Manager**:
   - Go to the AWS Console
   - Navigate to Secrets Manager > Secrets
   - Check the value of your agent secrets

2. **For .env file**:
   - Verify the .env file has been correctly copied into the Docker image
   - Check the container logs for any environment variable related errors

## Cleaning Up

To destroy all AWS resources created by Terraform:

```bash
cd ~/agentic/terraform  # Navigate to the terraform directory
terraform destroy
```

You'll need to confirm the deletion by typing `yes` when prompted.

## Customizing Your Deployment

### Scaling Your Agent

To scale your agent deployment, adjust the following in `terraform/terraform.tfvars`:

```hcl
service_desired_count = 2  # Number of instances to run
task_cpu = "2048"          # CPU units (1024 = 1 vCPU)
task_memory = "4096"       # Memory in MB
```

### Using a Custom Domain

To use a custom domain with your agent API:

1. Create an HTTPS certificate in AWS Certificate Manager
2. Configure an HTTPS listener on the load balancer
3. Create a DNS record pointing to the load balancer

Refer to AWS documentation for detailed instructions.
