# AWS Region
aws_region = "us-east-1"

# Network Settings
vpc_cidr            = "10.0.0.0/16"
availability_zones  = ["us-east-1a", "us-east-1b"]
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnet_cidrs = ["10.0.101.0/24", "10.0.102.0/24"]

# Project and Environment
project = "agentic"
environment = "dev"

# Common Tags
common_tags = {
  Project     = "agentic"
  Environment = "dev"
  Terraform   = "true"
}

# Deployment Mode - options: "api" or "dashboard"
deployment_mode = "api"

# ECS Settings
task_cpu              = "1024"  # 1 vCPU
task_memory           = "2048"  # 2 GB
service_desired_count = 1

# Ports
agent_port     = 8086
dashboard_port = 3000

# Agent Settings
agent_path  = "agents/basic_agent.py"  # Path to your agent file
user_agents = false  # Set to true if you want to enable user-specific agents
use_ray     = false  # Set to true if you want to use Ray for agent execution

# Replace these with your actual API keys in a secure way - DO NOT commit this file with real values
secrets_values = {
  OPENAI_API_KEY    = "your-openai-api-key"
  ANTHROPIC_API_KEY = "your-anthropic-api-key"
}

# Mapping of environment variables to secrets
secrets_env_mapping = {
  "OPENAI_API_KEY"    = "OPENAI_API_KEY"
  "ANTHROPIC_API_KEY" = "ANTHROPIC_API_KEY"
}
