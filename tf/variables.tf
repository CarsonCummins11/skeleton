variable "domain_name" {
  default = "your-app.com" # Replace with your domain
}

variable "api_domain_prefix" {
  default = "api"
}

variable "health_check_path" {
  default = "/health"
}

variable "db_username" {
  type    = string
  default = "postgres_admin"
}

variable "db_password" {
  type    = string
  default = "password123" # Override this in production via secrets
}
