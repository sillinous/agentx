// Provider configuration example for AWS. Configure credentials via env or shared config.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  # credentials: use AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars or shared credentials
}
