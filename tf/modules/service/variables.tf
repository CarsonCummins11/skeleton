variable "domain_name" {
  type    = string
}
variable "db_username" {
  type    = string
}
variable "db_password" {
  type    = string
}
variable "db_storage_size" {
  type    = number
  default = 10
}
variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "health_check_path" {
  type    = string
  default = "/health"
}
variable "max_api_ecs_host_count" {
    type    = number
    default = 5
}
variable "min_api_ecs_host_count" {
    type    = number
    default = 2
}
variable "api_ecs_host_cpu" {
    type    = number
    default = 256
}
variable "api_ecs_host_memory" {
    type    = number
    default = 512
}
variable "api_ecs_host_instance_type" {
    type    = string
    default = "t3.micro"
}
variable "api_ecs_host_volume_size" {
    type    = number
    default = 20
}

variable "worker_ecs_host_cpu" {
    type    = number
    default = 256
}
variable "worker_ecs_host_memory" {
    type    = number
    default = 512
}
variable "worker_ecs_host_instance_type" {
    type    = string
    default = "t3.micro"
}
variable "worker_ecs_host_volume_size" {
    type    = number
    default = 20
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "frontend_url" {
  type = string
}