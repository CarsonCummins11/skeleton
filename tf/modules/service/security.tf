resource "aws_security_group" "lb" {
    name        = "api-load-balancer-security-group"
    description = "controls access to the ALB"
    vpc_id      = aws_vpc.main.id

    ingress {
        protocol    = "tcp"
        from_port   = 443
        to_port     = 443
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        protocol    = "tcp"
        from_port   = 8000
        to_port     = 8000
        cidr_blocks = ["0.0.0.0/0"]
    }
}

# Traffic to the ECS cluster should only come from the ALB
resource "aws_security_group" "ecs_sg" {
  vpc_id = aws_vpc.main.id
  name   = "ecs-security-group"
  # Inbound and outbound rules
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.lb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# iam role for ECS tasks
resource "aws_iam_role" "ecs_execution_role" {
  name = "ecs_execution_role"

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

resource "aws_iam_role_policy_attachment" "ecs_execution_ecr_readonly" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ecs_execution_logs" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}