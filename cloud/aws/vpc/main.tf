# AWS VPC Infrastructure for Pulse Retrodiction Training POC
# This Terraform configuration sets up the basic VPC infrastructure

provider "aws" {
  region = var.aws_region
}

# VPC Definition
resource "aws_vpc" "retrodiction_poc_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "retrodiction-poc-vpc"
    Environment = var.environment
    Project     = var.project
  }
}

# Internet Gateway for public subnets
resource "aws_internet_gateway" "retrodiction_poc_igw" {
  vpc_id = aws_vpc.retrodiction_poc_vpc.id

  tags = {
    Name        = "retrodiction-poc-igw"
    Environment = var.environment
    Project     = var.project
  }
}

# Public Subnets (in different availability zones)
resource "aws_subnet" "public_subnets" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.retrodiction_poc_vpc.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "public-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = var.project
  }
}

# Private Subnets (in different availability zones)
resource "aws_subnet" "private_subnets" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.retrodiction_poc_vpc.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name        = "private-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = var.project
  }
}

# NAT Gateway for private subnets (requires an Elastic IP)
resource "aws_eip" "nat_eip" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnet_cidrs)) : 0
  domain = "vpc"
  
  tags = {
    Name        = var.single_nat_gateway ? "retrodiction-poc-nat-eip" : "retrodiction-poc-nat-eip-${count.index + 1}"
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_nat_gateway" "retrodiction_poc_nat" {
  count         = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnet_cidrs)) : 0
  allocation_id = aws_eip.nat_eip[count.index].id
  subnet_id     = aws_subnet.public_subnets[count.index].id

  tags = {
    Name        = var.single_nat_gateway ? "retrodiction-poc-nat" : "retrodiction-poc-nat-${count.index + 1}"
    Environment = var.environment
    Project     = var.project
  }

  # To ensure proper ordering, add this explicit dependency
  depends_on = [aws_internet_gateway.retrodiction_poc_igw]
}

# Route Table for Public Subnets
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.retrodiction_poc_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.retrodiction_poc_igw.id
  }

  tags = {
    Name        = "public-route-table"
    Environment = var.environment
    Project     = var.project
  }
}

# Route Tables for Private Subnets
resource "aws_route_table" "private_route_tables" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.private_subnet_cidrs)) : 0
  vpc_id = aws_vpc.retrodiction_poc_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.retrodiction_poc_nat[0].id : aws_nat_gateway.retrodiction_poc_nat[count.index].id
  }

  tags = {
    Name        = var.single_nat_gateway ? "private-route-table" : "private-route-table-${count.index + 1}"
    Environment = var.environment
    Project     = var.project
  }
}

# Route Table Associations for Public Subnets
resource "aws_route_table_association" "public_subnet_associations" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_route_table.id
}

# Route Table Associations for Private Subnets
resource "aws_route_table_association" "private_subnet_associations" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = var.enable_nat_gateway ? (var.single_nat_gateway ? aws_route_table.private_route_tables[0].id : aws_route_table.private_route_tables[count.index].id) : aws_route_table.public_route_table.id
}

# Security Group for retrodiction training services
resource "aws_security_group" "retrodiction_training_sg" {
  name        = "retrodiction-training-sg"
  description = "Security group for retrodiction training services"
  vpc_id      = aws_vpc.retrodiction_poc_vpc.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "retrodiction-training-sg"
    Environment = var.environment
    Project     = var.project
  }
}