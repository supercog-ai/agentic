# Updating Your Agentic Agent on AWS

This guide covers the process of updating your Agentic agent that has been deployed to AWS using the deployment process outlined in the Agentic AWS Deployment Guide.

## Prerequisites

Before updating your agent, ensure you have:

- Access to your Agentic project codebase
- AWS CLI installed and configured
- Docker installed and running
- The necessary permissions to push to ECR and update ECS services

## Step 1: Update Your Agent Code

Modify your agent file in the `agents` directory with your desired changes:

```python
from agentic.common import Agent, AgentRunner
from agentic.tools import WeatherTool, GoogleNewsTool

# Update model, tools, instructions, etc.
updated_agent = Agent(
    name="Weather Agent 2.0",
    welcome="I can now give you detailed weather reports and the news!",
    instructions="You are a helpful assistant specializing in comprehensive weather information and current events.",
    tools=[WeatherTool(), GoogleNewsTool()],
    model="openai/gpt-4o"  # Upgraded model
)

if __name__ == "__main__":
    AgentRunner(updated_agent).repl_loop()
```

Common updates include:
- Adding new tools or capabilities
- Upgrading the underlying model
- Refining the agent's instructions or prompt engineering
- Implementing additional business logic
- Improving error handling

## Step 2: Test Your Changes Locally

Before deploying to AWS, test your updates locally to ensure they work as expected:

```bash
# Activate your virtual environment
cd ~/agentic
source .venv/bin/activate

# Run your updated agent
python agents/your_updated_agent.py
```

Test all the new functionality and ensure there are no regressions in existing capabilities.

## Step 3: Update Configuration (If Needed)

If you've made changes that require configuration updates, modify your `terraform.tfvars` file:

```bash
cd deployment/terraform
```

Edit `terraform.tfvars` to update relevant settings:

```hcl
# Update agent path if you renamed or moved the agent file
agent_path = "agents/your_updated_agent.py"

# Update resource allocations if needed for larger models
task_cpu    = "2048"  # 2 vCPU
task_memory = "4096"  # 4 GB

# Update any other relevant configuration variables
use_ray     = true    # Enable Ray for parallel processing if needed
```

If you've updated the configuration, apply the Terraform changes:

```bash
terraform plan    # Review the planned changes
terraform apply   # Apply the changes
```

## Step 4: Rebuild and Push the Docker Image

Build a new Docker image with your updated code:

```bash
# Navigate to the project root
cd ~/agentic

# Get your ECR repository URL
export AWS_REGION=$(aws configure get region)
export ECR_REPO_URL=$(cd deployment/terraform && terraform output -raw ecr_repository_url)

# Log in to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URL}
```

Build and push the appropriate Docker image based on your deployment mode:

```bash
# For API Server Deployment
docker build --platform linux/amd64 --tag ${ECR_REPO_URL}:latest --file deployment/Dockerfile.api .
docker push ${ECR_REPO_URL}:latest

# OR

# For Dashboard Deployment
docker build --platform linux/amd64 --tag ${ECR_REPO_URL}:latest --file deployment/Dockerfile.dashboard .
docker push ${ECR_REPO_URL}:latest
```

## Step 5: Force a New Deployment

ECS doesn't automatically detect when you've pushed a new image with the same tag. You need to force a new deployment to apply your updates:

```bash
# Get the ECS cluster and service names
export ECS_CLUSTER=$(cd deployment/terraform && terraform output -raw ecs_cluster_name)
export ECS_SERVICE=$(cd deployment/terraform && terraform output -raw ecs_service_name)

# Force a new deployment
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment
```

## Step 6: Monitor the Deployment

Monitor the deployment to ensure your updates are being applied successfully:

```bash
# Check deployment status
aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query "services[0].deployments"
```

You should see a new deployment in progress with the status `PRIMARY` and the old deployment with the status `ACTIVE`. Once the new deployment is complete, the old deployment will be removed.

Check the CloudWatch logs for any issues:

```bash
# Get the name of the latest log stream
LATEST_LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name "/ecs/${ECS_CLUSTER}" \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --query "logStreams[0].logStreamName" \
  --output text)

# View the logs
aws logs get-log-events \
  --log-group-name "/ecs/${ECS_CLUSTER}" \
  --log-stream-name "$LATEST_LOG_STREAM"
```

## Step 7: Test the Updated Deployment

Test your updated agent to ensure everything is working as expected:

```bash
# Get the endpoint URL
export AGENT_ENDPOINT=$(cd deployment/terraform && terraform output -raw agent_endpoint)
```

### For API Server Deployments

```bash
# Test the discovery endpoint
curl "$AGENT_ENDPOINT/_discovery"

# Test your agent
curl -X POST "$AGENT_ENDPOINT/your-agent-name/process" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test the new features"}'
```

### For Dashboard Deployments

Open a web browser and navigate to:

```
http://$AGENT_ENDPOINT
```

Interact with your agent through the dashboard interface to ensure it's working correctly.

## Advanced Update Strategies

### Using Image Versioning

Instead of always using the `latest` tag, consider implementing versioning for your Docker images:

```bash
# Tag with version number
export VERSION="1.2.0"
docker build --platform linux/amd64 --tag ${ECR_REPO_URL}:${VERSION} --file deployment/Dockerfile.api .
docker push ${ECR_REPO_URL}:${VERSION}

# Also update latest for backward compatibility
docker tag ${ECR_REPO_URL}:${VERSION} ${ECR_REPO_URL}:latest
docker push ${ECR_REPO_URL}:latest
```

Update your task definition to use the specific version:

```hcl
container_definitions = jsonencode([
  {
    name  = var.project
    image = "${aws_ecr_repository.app.repository_url}:1.2.0"
    # ...other config
  }
])
```

### Rolling Back Updates

If you need to roll back to a previous version:

1. Push the previous version image or use an existing tagged version
2. Update the task definition to use the previous version
3. Force a new deployment

```bash
# Update task definition to use previous version
# (Edit in Terraform or via AWS Console)

# Force a new deployment
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment
```

### Blue/Green Deployments

For zero-downtime updates, consider implementing blue/green deployments:

1. Deploy the new version to a new ECS service
2. Test the new deployment
3. Switch the load balancer target group to the new service
4. Terminate the old service once traffic is successfully routed

This requires additional Terraform configuration but provides safer updates for production environments.

## Maintaining a Changelog

For better tracking of agent changes, maintain a changelog in your project:

```markdown
# Changelog

## v1.2.0 (2025-05-15)
- Added climate history tool
- Upgraded to GPT-4o model
- Improved error handling for API rate limits

## v1.1.0 (2025-04-10)
- Added forecast capability
- Expanded location support
- Fixed bug in temperature conversion

## v1.0.0 (2025-03-01)
- Initial release
- Basic weather information support
```

## Automating Updates with CI/CD

Consider setting up a CI/CD pipeline (using GitHub Actions, GitLab CI, or AWS CodePipeline) to automate the update process:

1. Push changes to your repository
2. Automated tests run to validate the changes
3. Docker image is built and pushed to ECR
4. ECS service is updated with the new image
5. Post-deployment tests verify the update

This provides a more streamlined and reliable update process for production environments.

## Troubleshooting Updates

### New Deployment Won't Start

If the new task won't start:

1. Check the task definition for any issues
2. Verify resource constraints (CPU/memory)
3. Check the Docker image exists in ECR
4. Look for errors in the CloudWatch logs

### Service Unhealthy After Update

If the service is unhealthy after the update:

1. Check that health check endpoints are working
2. Verify the agent is starting up correctly
3. Check for any runtime errors in the logs
4. Ensure the correct ports are exposed

### Agent Not Behaving as Expected

If the agent isn't working as expected after the update:

1. Verify the correct agent file is being used
2. Check environment variables and secrets are properly set
3. Verify API keys are valid and have sufficient quota
4. Test the specific functionality that's not working correctly
