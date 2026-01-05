output "s3_bucket_name" {
  value = aws_s3_bucket.media_bucket.bucket
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "db_instance_id" {
  value = aws_db_instance.postgres.id
}
