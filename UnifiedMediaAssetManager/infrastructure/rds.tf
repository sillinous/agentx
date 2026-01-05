// NOTE: This is a simplified example. Production RDS should be deployed in DB subnets (private) and with proper security groups.
resource "aws_db_subnet_group" "default" {
  name       = "umam-db-subnet-group"
  subnet_ids = [] # <--- populate with private subnet IDs
  tags = {
    Name = "umam-db-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier = var.db_identifier
  engine     = "postgres"
  instance_class = var.db_instance_class
  allocated_storage = 20
  name = var.db_name
  username = var.db_username
  password = var.db_password
  skip_final_snapshot = true
  publicly_accessible = false
  db_subnet_group_name = aws_db_subnet_group.default.name

  tags = {
    Name = "umam-db"
    Env  = "dev"
  }
}
