resource "aws_db_subnet_group" "main" {
  name       = "api-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags = {
    Name = "api-db-subnet-group"
  }
}


resource "aws_security_group" "rds" {
  name        = "api-rds-sg"
  description = "Allow Postgres access from ECS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
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

resource "aws_db_instance" "main" {
  identifier              = "api-db"
  engine                  = "postgres"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_storage_size
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  skip_final_snapshot     = true
  publicly_accessible     = false
  multi_az                = false
  storage_encrypted       = true
  deletion_protection     = false
}

output "rds_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "rds_connection_string" {
  value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/postgres"
}
