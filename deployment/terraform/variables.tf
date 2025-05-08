variable "project" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "agentic"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "agentic"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "task_cpu" {
  description = "CPU units for the ECS task"
  type        = string
  default     = "1024"  # 1 vCPU
}

variable "task_memory" {
  description = "Memory for the ECS task in MiB"
  type        = string
  default     = "2048"  # 2 GB
}

variable "service_desired_count" {
  description = "Number of task instances to run"
  type        = number
  default     = 1
}

variable "deployment_mode" {
  description = "Deployment mode - either 'api' or 'dashboard'"
  type        = string
  default     = "api"
  validation {
    condition     = contains(["api", "dashboard"], var.deployment_mode)
    error_message = "The deployment_mode must be either 'api' or 'dashboard'."
  }
}

variable "agent_path" {
  description = "Path to the agent file inside the container"
  type        = string
  default     = "agents/basic_agent.py"
}

variable "agent_port" {
  description = "Port for the agent api to expose"
  type        = number
  default     = 8086
}

variable "dashboard_port" {
  description = "Port for the dashboard expose"
  type        = number
  default     = 3000
}

variable "user_agents" {
  description = "Enable user-specific agents"
  type        = bool
  default     = false
}

variable "use_ray" {
  description = "Use Ray for agent execution"
  type        = bool
  default     = false
}

variable "secrets_values" {
  description = "Map of secrets to store in SecretsManager (insecure for actual secrets)"
  type        = map(string)
  default     = {
    OPENAI_API_KEY     = "your-openai-api-key"
    ANTHROPIC_API_KEY  = "your-anthropic-api-key"
  }
  sensitive   = true
}

variable "secrets_env_mapping" {
  description = "Mapping between environment variable names and JSON keys in the secret"
  type        = map(string)
  default     = {
    OPENAI_API_KEY     = "OPENAI_API_KEY"
    ANTHROPIC_API_KEY  = "ANTHROPIC_API_KEY"
  }
}
