terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Uncomment to use Terraform Cloud for state management
  # backend "remote" {
  #   organization = "your-org-name"
  #   workspaces {
  #     name = "agentic-api-workspace"
  #   }
  # }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Network Configuration
module "vpc" {
  source = "./modules/vpc"

  vpc_name        = var.vpc_name
  vpc_cidr        = var.vpc_cidr
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
}

# ECR Repository
resource "aws_ecr_repository" "agentic_api" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "agentic_cluster" {
  name = var.ecs_cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# SecretsManager for storing environment variables
resource "aws_secretsmanager_secret" "agentic_secrets" {
  name                    = var.secrets_name
  recovery_window_in_days = 0  # Set to 0 for easier testing/development, use 7+ for production
}

# Example of creating a secret value - in production you'd use more secure methods
resource "aws_secretsmanager_secret_version" "agentic_secrets_version" {
  secret_id     = aws_secretsmanager_secret.agentic_secrets.id
  secret_string = jsonencode(var.secrets_values)
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "agentic-ecs-task-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow access to Secrets Manager
resource "aws_iam_policy" "secrets_access" {
  name        = "agentic-secrets-access"
  description = "Allow ECS tasks to access Agentic secrets in Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.agentic_secrets.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_access_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# ECS Task Definition
resource "aws_ecs_task_definition" "agentic_api" {
  family                   = "agentic-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "agentic-api"
      image     = "${aws_ecr_repository.agentic_api.repository_url}:latest"
      essential = true
      
      portMappings = [
        {
          containerPort = 8086
          hostPort      = 8086
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "AGENT_PATH"
          value = var.agent_path
        },
        {
          name  = "AGENT_PORT"
          value = "8086"
        },
        {
          name  = "USER_AGENTS"
          value = tostring(var.user_agents)
        },
        {
          name  = "USE_RAY"
          value = tostring(var.use_ray)
        }
      ]
      
      secrets = [for key, value in var.secrets_env_mapping : {
        name      = key
        valueFrom = "${aws_secretsmanager_secret.agentic_secrets.arn}:${value}::"
      }]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.agentic_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "agentic"
        }
      }
    }
  ])
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "agentic_logs" {
  name              = "/ecs/agentic-api"
  retention_in_days = 30
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "agentic-ecs-tasks"
  description = "Allow inbound traffic to Agentic API"
  vpc_id      = module.vpc.vpc_id

  ingress {
    protocol         = "tcp"
    from_port        = 8086
    to_port          = 8086
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "agentic-alb"
  description = "Allow inbound traffic to ALB"
  vpc_id      = module.vpc.vpc_id

  ingress {
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

# Application Load Balancer
resource "aws_lb" "agentic_alb" {
  name               = "agentic-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnet_ids

  enable_deletion_protection = false
}

resource "aws_lb_target_group" "agentic_api" {
  name        = "agentic-api"
  port        = 8086
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    interval            = 30
    path                = "/_discovery"
    port                = "traffic-port"
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
    matcher             = "200"
  }
}

resource "aws_lb_listener" "agentic_http" {
  load_balancer_arn = aws_lb.agentic_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.agentic_api.arn
  }
}

# ECS Service
resource "aws_ecs_service" "agentic_api" {
  name            = "agentic-api"
  cluster         = aws_ecs_cluster.agentic_cluster.id
  task_definition = aws_ecs_task_definition.agentic_api.arn
  desired_count   = var.service_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.agentic_api.arn
    container_name   = "agentic-api"
    container_port   = 8086
  }

  depends_on = [
    aws_lb_listener.agentic_http
  ]
}
