terraform {
  backend "s3" {
    encrypt = true
    bucket  = "your-app-tf-state"         # Replace with your S3 bucket name
    key     = "your-app/terraform.tfstate" # Replace with your state key
    region  = "us-east-1"
  }
}
