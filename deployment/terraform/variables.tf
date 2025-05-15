variable "aws_region" {
  description = "AWS Region for resource deployment"
  type        = string
}

variable "vpc_name" {
  description = "Name of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "project" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "deployment_mode" {
  description = "Deployment mode - options: 'api' or 'dashboard'"
  type        = string
}

variable "task_cpu" {
  description = "CPU units for the ECS task"
  type        = string
}

variable "task_memory" {
  description = "Memory for the ECS task (in MB)"
  type        = string
}

variable "service_desired_count" {
  description = "Desired count of tasks for the ECS service"
  type        = number
}

variable "agent_path" {
  description = "Path to the agent file"
  type        = string
}

variable "user_agents" {
  description = "Whether to enable user-specific agents"
  type        = bool
}

variable "use_ray" {
  description = "Whether to use Ray for agent execution"
  type        = bool
}

variable "agent_port" {
  description = "Port for the agent service"
  type        = number
}

variable "dashboard_port" {
  description = "Port for the dashboard service"
  type        = number
}

variable "secrets_values" {
  description = "Map of secret values to store in Secrets Manager"
  type        = map(string)
  sensitive   = true
}

variable "secrets_env_mapping" {
  description = "Mapping of environment variables to secret values"
  type        = map(string)
}
