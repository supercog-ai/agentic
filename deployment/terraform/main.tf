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
  #     name = "${var.project}-workspace"
  #   }
  # }
}

provider "aws" {
  region = var.aws_region
}

# Local values for name prefixing
locals {
  name_prefix = "${var.project}-${var.environment}"
}

# VPC and Network Configuration
module "vpc" {
  source = "./modules/vpc"

  vpc_name        = "${local.name_prefix}-vpc"
  vpc_cidr        = var.vpc_cidr
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# ECR Repository
resource "aws_ecr_repository" "app" {
  name                 = "${local.name_prefix}-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = var.common_tags
}

# ECS Cluster
resource "aws_ecs_cluster" "app_cluster" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = var.common_tags
}

# SecretsManager for storing environment variables
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${local.name_prefix}-secrets"
  recovery_window_in_days = 0  # Set to 0 for easier testing/development, use 7+ for production
  
  tags = var.common_tags
}

# Example of creating a secret value - in production you'd use more secure methods
resource "aws_secretsmanager_secret_version" "app_secrets_version" {
  secret_id     = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode(var.secrets_values)
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${local.name_prefix}-ecs-task-exec-role"
  
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
  
  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow access to Secrets Manager
resource "aws_iam_policy" "secrets_access" {
  name        = "${local.name_prefix}-secrets-access"
  description = "Allow ECS tasks to access ${var.project} secrets in Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.app_secrets.arn
      }
    ]
  })
  
  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "secrets_access_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = local.name_prefix
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = var.project
      image     = "${aws_ecr_repository.app.repository_url}:latest"
      essential = true
      
      portMappings = var.deployment_mode == "dashboard" ? [
        {
          containerPort = var.dashboard_port
          hostPort      = var.dashboard_port
          protocol      = "tcp"
        }
      ] : [
        {
          containerPort = var.agent_port
          hostPort      = var.agent_port
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
          value = tostring(var.agent_port)
        },
        {
          name  = "DASHBOARD_PORT"
          value = tostring(var.dashboard_port)
        },
        {
          name  = "USER_AGENTS"
          value = tostring(var.user_agents)
        },
        {
          name  = "USE_RAY"
          value = tostring(var.use_ray)
        },
        {
          name  = "DEPLOYMENT_MODE"
          value = var.deployment_mode
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
      
      secrets = [for key, value in var.secrets_env_mapping : {
        name      = key
        valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:${value}::"
      }]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = var.project
        }
      }
    }
  ])
  
  tags = var.common_tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 30
  
  tags = var.common_tags
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${local.name_prefix}-ecs-tasks-sg"
  description = "Allow inbound traffic to ${var.project} API or Dashboard"
  vpc_id      = module.vpc.vpc_id

  ingress {
    protocol         = "tcp"
    from_port        = var.deployment_mode == "dashboard" ? var.dashboard_port : var.agent_port
    to_port          = var.deployment_mode == "dashboard" ? var.dashboard_port : var.agent_port
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
  
  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-ecs-tasks-sg"
  })
}

# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
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
  
  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

# Application Load Balancer
resource "aws_lb" "app_alb" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnet_ids

  enable_deletion_protection = false
  
  tags = var.common_tags
}

resource "aws_lb_target_group" "app" {
  name        = "${local.name_prefix}-tg"
  port        = var.deployment_mode == "dashboard" ? var.dashboard_port : var.agent_port
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    interval            = 30
    path                = var.deployment_mode == "dashboard" ? "/api/_discovery" : "/_discovery"
    port                = "traffic-port"
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
    matcher             = "200"
  }
  
  tags = var.common_tags
}

resource "aws_lb_listener" "app_http" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
  
  tags = var.common_tags
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${local.name_prefix}-service"
  cluster         = aws_ecs_cluster.app_cluster.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.service_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.project
    container_port   = var.deployment_mode == "dashboard" ? var.dashboard_port : var.agent_port
  }

  depends_on = [
    aws_lb_listener.app_http
  ]
  
  tags = var.common_tags
}
