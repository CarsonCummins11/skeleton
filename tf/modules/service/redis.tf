# Security group for Redis - only allows access from ECS
resource "aws_security_group" "redis" {
  name        = "redis-security-group"
  description = "Security group for Redis clusters - only allows access from ECS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }

  ingress {
    from_port       = 6380
    to_port         = 6380
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_cluster" "redis-cache" {
  cluster_id           = "cluster-${local.subdomain}"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
}

resource "aws_elasticache_cluster" "redis-pubsub" {
  cluster_id           = "cluster-${local.subdomain}-pubsub"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6380
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
}

# Subnet group for Redis clusters
resource "aws_elasticache_subnet_group" "redis" {
  name       = "redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}