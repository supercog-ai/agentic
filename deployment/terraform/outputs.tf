output "ecr_repository_url" {
  description = "The ECR repository URL where you should push your Docker image"
  value       = aws_ecr_repository.agent_repository.repository_url
}

output "agent_endpoint" {
  description = "The endpoint where the agent API can be accessed"
  value       = aws_lb.agentic_alb.dns_name
}
