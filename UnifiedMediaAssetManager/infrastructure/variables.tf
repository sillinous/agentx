variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket" {
  description = "Name of the S3 bucket to create for media (must be globally unique)"
  type        = string
}

variable "db_identifier" {
  description = "RDS instance identifier"
  type        = string
  default     = "umam-db"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "umam"
}

variable "db_username" {
  description = "Master DB username"
  type        = string
  default     = "umam_admin"
}

variable "db_password" {
  description = "Master DB password (supply securely in production)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}
