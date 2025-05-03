for # Output definitions for the VPC infrastructure

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.retrodiction_poc_vpc.id
}

output "vpc_cidr" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.retrodiction_poc_vpc.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = aws_subnet.private_subnets[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.retrodiction_poc_nat[*].id
}

output "security_group_id" {
  description = "ID of the security group for the retrodiction training services"
  value       = aws_security_group.retrodiction_training_sg.id
}

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public_route_table.id
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables"
  value       = aws_route_table.private_route_tables[*].id
}