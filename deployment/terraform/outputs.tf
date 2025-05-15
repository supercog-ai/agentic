output "ecr_repository_url" {
  description = "The ECR repository URL where you should push your Docker image"
  value       = aws_ecr_repository.app.repository_url
}

output "agent_endpoint" {
  description = "The endpoint where the agent API can be accessed"
  value       = aws_lb.app_alb.dns_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster where the service is running"
  value       = aws_ecs_cluster.app_cluster.name
}

output "ecs_service_name" {
  description = "The name of the ECS service"
  value       = aws_ecs_service.app.name
}
