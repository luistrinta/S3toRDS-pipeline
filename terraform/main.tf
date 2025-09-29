provider "aws" {
  region = "eu-west-2"
}

# S3 bucket with lifecycle rule
resource "aws_s3_bucket" "lambda_bucket" {
  bucket = "s3-to-pg-bucket-dev" # change dev to ${random_id.bucket_id.hex} for production
  acl    = "private"

  lifecycle_rule {
    id      = "auto-delete-30-days"
    enabled = true

    expiration {
      days = 30
    }
  }
}

resource "random_id" "bucket_id" {
  byte_length = 4
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "lambda_s3_to_pg_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy attachment for logging and S3 access
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Lambda function (placeholder zip must exist)
resource "aws_lambda_function" "s3_to_pg" {
  function_name = "S3ToPG"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "lambda_function_cloud.lambda_handler"
  runtime       = "python3.12"
  architectures = ["x86_64"]
  filename      = "lambda_function_cloud.zip" # You must provide this package
}

# Allow S3 to invoke Lambda
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_to_pg.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.lambda_bucket.arn
}

# S3 event notification
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.lambda_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_to_pg.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}

# Security group for RDS (kept simple for free tier)
resource "aws_security_group" "rds_sg" {
  name        = "rds-public-sg"
  description = "Allow PostgreSQL inbound"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
}

# Subnet in eu-west-2a
resource "aws_subnet" "subnet_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-west-2a"
  map_public_ip_on_launch = true
}

# Subnet in eu-west-2b
resource "aws_subnet" "subnet_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "eu-west-2b"
  map_public_ip_on_launch = true
}

# DB Subnet Group across 2 AZs
resource "aws_db_subnet_group" "main" {
  name       = "main-subnet-group"
  subnet_ids = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
}

# Internet Gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

# Associate route table with subnets
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.subnet_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "b" {
  subnet_id      = aws_subnet.subnet_b.id
  route_table_id = aws_route_table.public.id
}


# RDS PostgreSQL - free tier eligible (db.t3.micro, 20GB)
resource "aws_db_instance" "postgres" {
  identifier             = "s3topgdb"
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "17.4"
  instance_class         = "db.t4g.micro"
  username               = "postgresadmin"
  password               = "YourPassword123!"
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  skip_final_snapshot    = true
}

