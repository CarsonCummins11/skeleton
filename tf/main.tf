terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "client" {
  source = "./modules/static_site"

  domain_name = var.domain_name
}

module "api" {
  source                        = "./modules/service"
  domain_name                   = "${var.api_domain_prefix}.${var.domain_name}"
  health_check_path             = var.health_check_path
  max_api_ecs_host_count        = 4
  min_api_ecs_host_count        = 2
  api_ecs_host_cpu              = 256
  api_ecs_host_memory           = 512
  api_ecs_host_instance_type    = "t3.micro"
  api_ecs_host_volume_size      = 20
  worker_ecs_host_cpu           = 256
  worker_ecs_host_memory        = 512
  worker_ecs_host_instance_type = "t3.micro"
  worker_ecs_host_volume_size   = 20
  db_username                   = var.db_username
  db_password                   = var.db_password
  frontend_url                  = var.domain_name
}
