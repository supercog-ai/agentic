variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "vpc_name" {
  description = "Name of the VPC"
  type        = string
  default     = "agentic-vpc"
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

variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "agentic-api"
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "agentic-cluster"
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

variable "agent_path" {
  description = "Path to the agent file inside the container"
  type        = string
  default     = "agents/basic_agent.py"
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

variable "secrets_name" {
  description = "Name of the SecretsManager secret"
  type        = string
  default     = "agentic-api-secrets"
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
