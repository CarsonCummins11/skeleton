# ecr repo for the api image
resource "aws_ecr_repository" "service_repo" {
  name = "${local.subdomain}-service-repo"
}

# ecr repo for the worker image
resource "aws_ecr_repository" "worker_repo" {
  name = "${local.subdomain}-worker-repo"
}