# AWS VPC Infrastructure for Pulse Retrodiction POC

This directory contains Terraform configuration for setting up the AWS VPC infrastructure required for the Pulse retrodiction training Proof of Concept (POC). The infrastructure provides a secure, isolated network environment for running retrodiction training workloads in the cloud.

## Infrastructure Components

The Terraform configuration creates the following AWS resources:

- **VPC**: A dedicated Virtual Private Cloud with customizable CIDR range
- **Subnets**: Public and private subnets spread across multiple availability zones
- **Internet Gateway**: Allows public subnets to access the internet
- **NAT Gateway**: Enables instances in private subnets to access the internet while remaining private
- **Route Tables**: Configures network routing for public and private subnets
- **Security Groups**: Basic security controls for retrodiction training services

## Architecture Design

The infrastructure follows a standard pattern for secure AWS networking:

```
                                  │
                                  │ Internet
                                  │
                                  ▼
                           ┌──────────────┐
                           │Internet Gateway│
                           └──────────────┘
                                  │
                                  │
        ┌─────────────────────────────────────────┐
        │                  VPC                    │
        │                                         │
        │  ┌─────────────┐       ┌─────────────┐  │
        │  │Public Subnet│       │Public Subnet│  │
        │  │     AZ1     │       │     AZ2     │  │
        │  └─────────────┘       └─────────────┘  │
        │          │                    │         │
        │          ▼                    │         │
        │    ┌──────────┐               │         │
        │    │    NAT   │               │         │
        │    │  Gateway │               │         │
        │    └──────────┘               │         │
        │          │                    │         │
        │          ▼                    ▼         │
        │  ┌─────────────┐       ┌─────────────┐  │
        │  │Private Subnet│      │Private Subnet│  │
        │  │     AZ1     │      │     AZ2     │  │
        │  └─────────────┘      └─────────────┘  │
        │                                         │
        └─────────────────────────────────────────┘
```

This architecture provides:

1. **Availability**: Resources are spread across multiple availability zones for high availability
2. **Security**: Private subnets isolate sensitive processing workloads
3. **Connectivity**: NAT Gateway allows private instances to download dependencies and send logs
4. **Scalability**: Modular design supports adding more resources as needed

## Usage

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform v1.0.0 or newer

### Configuration

Edit the `variables.tf` file to customize:

- AWS region
- VPC CIDR block
- Subnet CIDR blocks
- Availability zones
- Environment tags

### Deployment

1. Initialize Terraform:
   ```
   terraform init
   ```

2. Plan the deployment:
   ```
   terraform plan
   ```

3. Apply the configuration:
   ```
   terraform apply
   ```

4. To destroy the infrastructure when no longer needed:
   ```
   terraform destroy
   ```

## Outputs

After deployment, Terraform will output:

- VPC ID
- Subnet IDs (public and private)
- Security Group ID
- Route Table IDs

These can be used in subsequent Terraform configurations for deploying actual compute resources.

## Security Considerations

- The default security group only allows SSH inbound access and all outbound access
- For production use, restrict SSH access to known IP ranges
- Consider adding a bastion host for secure access to instances in private subnets
- Review and customize security groups based on specific application requirements

## Future Enhancements

- Add VPC endpoints for secure access to AWS services without internet exposure
- Implement AWS Network Firewall for enhanced traffic filtering
- Set up VPC Flow Logs for network monitoring and troubleshooting
- Add Transit Gateway for connecting to other VPCs or on-premises networks