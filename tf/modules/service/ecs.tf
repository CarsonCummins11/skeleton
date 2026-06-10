# shared environment variables list definition for ecs services
resource "random_password" "session_secret_key" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

locals {
  default_ecs_env_vars = [
        {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/postgres"
        },
        {
          name  = "DB_USERNAME"
          value = var.db_username
        },
        {
          name  = "DB_PASSWORD"
          value = var.db_password
        },
        {
          name = "CACHE_REDIS_URL"
          value = "redis://${aws_elasticache_cluster.redis-cache.cache_nodes[0].address}:${aws_elasticache_cluster.redis-cache.cache_nodes[0].port}"
        },
        {
          name = "PUBSUB_REDIS_URL"
          value = "redis://${aws_elasticache_cluster.redis-pubsub.cache_nodes[0].address}:${aws_elasticache_cluster.redis-pubsub.cache_nodes[0].port}"
        },
        {
          name = "FRONTEND_URL"
          value = "https://${var.frontend_url}"
        },
        {
          name = "ENVIRONMENT"
          value = "prod"
        },
        {
          name = "SESSION_SECRET_KEY",
          value = random_password.session_secret_key.result
        }
      ]
}



/*

Definition of ECS service for the API 

*/
resource "aws_ecs_task_definition" "api_task_definition" {
  family                = "api-task"
  network_mode          = "awsvpc"
  memory                = var.api_ecs_host_memory
  cpu                   = var.api_ecs_host_cpu
  requires_compatibilities = ["FARGATE"]

  execution_role_arn    = aws_iam_role.ecs_execution_role.arn

  # Container definition
  container_definitions = jsonencode([
    {
      name      = "${local.subdomain}-container"
      image     = "${aws_ecr_repository.service_repo.repository_url}:latest"
      cpu       = var.api_ecs_host_cpu
      memory    = var.api_ecs_host_memory
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = local.default_ecs_env_vars
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_service.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "${local.subdomain}"
        }
      }
    }
  ])
}

# ECS service
resource "aws_ecs_cluster" "api_ecs_cluster" {
  name = "${local.subdomain}-cluster"
}

resource "aws_ecs_service" "service" {
  name            = "${local.subdomain}-service"
  cluster         = aws_ecs_cluster.api_ecs_cluster.id
  task_definition = aws_ecs_task_definition.api_task_definition.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  depends_on      = [aws_alb_target_group.api]

  # Network configuration
  network_configuration {
    subnets          = aws_subnet.public.*.id
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  # Load balancer configuration
  load_balancer {
    target_group_arn = aws_alb_target_group.api.arn
    container_name   = "${local.subdomain}-container"
    container_port   = 8000
  }
}

# auto-scaling for ECS service
resource "aws_appautoscaling_target" "ecs_target" {
    max_capacity       = var.max_api_ecs_host_count
    min_capacity       = var.min_api_ecs_host_count
    resource_id        = "service/${aws_ecs_cluster.api_ecs_cluster.name}/${aws_ecs_service.service.name}"
    scalable_dimension = "ecs:service:DesiredCount"
    service_namespace  = "ecs"
}
resource "aws_appautoscaling_policy" "ecs_scale_out" {
    name                   = "ecs-scale-out"
    policy_type           = "StepScaling"
    resource_id            = aws_appautoscaling_target.ecs_target.resource_id
    scalable_dimension     = aws_appautoscaling_target.ecs_target.scalable_dimension
    service_namespace      = aws_appautoscaling_target.ecs_target.service_namespace

    step_scaling_policy_configuration {
        adjustment_type = "ChangeInCapacity"
        cooldown        = 60

        step_adjustment {
            scaling_adjustment = 1
            metric_interval_lower_bound = 0
        }
    }
}
resource "aws_appautoscaling_policy" "ecs_scale_in" {
    name                   = "ecs-scale-in"
    policy_type           = "StepScaling"
    resource_id            = aws_appautoscaling_target.ecs_target.resource_id
    scalable_dimension     = aws_appautoscaling_target.ecs_target.scalable_dimension
    service_namespace      = aws_appautoscaling_target.ecs_target.service_namespace

    step_scaling_policy_configuration {
        adjustment_type = "ChangeInCapacity"
        cooldown        = 60

        step_adjustment {
            scaling_adjustment = -1
            metric_interval_upper_bound = 0
        }
    }
}

# Scale out when average CPU > 75% for 2 minutes
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "ecs-cpu-utilization-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 75
  alarm_description   = "This metric monitors high CPU to trigger ECS scale out"
  dimensions = {
    ClusterName = aws_ecs_cluster.api_ecs_cluster.name
    ServiceName = aws_ecs_service.service.name
  }
  alarm_actions = [aws_appautoscaling_policy.ecs_scale_out.arn]
}

# Scale in when average CPU < 25% for 2 minutes
resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "ecs-cpu-utilization-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 25
  alarm_description   = "This metric monitors low CPU to trigger ECS scale in"
  dimensions = {
    ClusterName = aws_ecs_cluster.api_ecs_cluster.name
    ServiceName = aws_ecs_service.service.name
  }
  alarm_actions = [aws_appautoscaling_policy.ecs_scale_in.arn]
}

resource "aws_cloudwatch_log_group" "ecs_service" {
  name              = "/ecs/${local.subdomain}-service"
  retention_in_days = 7
}


/*

Definition of ECS service for the worker

*/
resource "aws_cloudwatch_log_group" "ecs_worker" {
  name              = "/ecs/${local.subdomain}-worker"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "worker_task_definition" {
  family                = "worker-task"
  network_mode          = "awsvpc"
  memory                = var.worker_ecs_host_memory
  cpu                   = var.worker_ecs_host_cpu
  requires_compatibilities = ["FARGATE"]

  execution_role_arn    = aws_iam_role.ecs_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "${local.subdomain}-worker-container"
      image     = "${aws_ecr_repository.worker_repo.repository_url}:latest"
      cpu       = var.worker_ecs_host_cpu
      memory    = var.worker_ecs_host_memory
      environment = local.default_ecs_env_vars
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "${local.subdomain}-worker"
        }
      }
    }
  ])
}

resource "aws_ecs_cluster" "worker_ecs_cluster" {
  name = "${local.subdomain}-worker-cluster"
}

resource "aws_ecs_service" "worker" {
  name            = "${local.subdomain}-worker"
  cluster         = aws_ecs_cluster.worker_ecs_cluster.id
  task_definition = aws_ecs_task_definition.worker_task_definition.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  # Network configuration
  network_configuration {
    subnets          = aws_subnet.public.*.id
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
}