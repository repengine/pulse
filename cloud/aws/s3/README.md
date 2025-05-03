# AWS S3 Buckets for Pulse Retrodiction POC

This directory contains Terraform configuration for setting up the AWS S3 infrastructure required for the Pulse retrodiction training Proof of Concept (POC). The infrastructure provides secure storage for both input data and output results of the retrodiction training process.

## Infrastructure Components

The Terraform configuration creates the following AWS resources:

- **S3 Buckets**: 
  - Data bucket for storing input datasets
  - Results bucket for storing training outputs and artifacts
- **Bucket Configurations**:
  - Versioning (optional)
  - Server-side encryption (optional)
  - Public access blocking (mandatory)
- **IAM Resources**:
  - IAM role for accessing S3 buckets
  - IAM policy with appropriate permissions for data access
  - Policy attachment to the IAM role

## Architecture Design

The infrastructure follows AWS best practices for secure S3 storage:

```
┌─────────────────────────┐              ┌─────────────────────────┐
│                         │              │                         │
│       Data Bucket       │              │     Results Bucket      │
│                         │              │                         │
│  ┌───────────────────┐  │              │  ┌───────────────────┐  │
│  │     Input Data    │  │              │  │  Training Results │  │
│  └───────────────────┘  │              │  └───────────────────┘  │
│                         │              │                         │
└─────────────────────────┘              └─────────────────────────┘
           ▲                                        ▲
           │                                        │
           │                                        │
           │                                        │
           │                                        │
           │                                        │
           │                                        │
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                       IAM Access Policies                        │
│                                                                  │
│  ┌────────────────────────────┐  ┌───────────────────────────┐  │
│  │  Read-only for Data Bucket │  │ Read/Write Results Bucket │  │
│  └────────────────────────────┘  └───────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                               ▲
                               │
                               │
         ┌────────────────────────────────────────┐
         │                                        │
         │         S3 Access IAM Role             │
         │                                        │
         └────────────────────────────────────────┘
                               ▲
                               │
                               │
         ┌────────────────────────────────────────┐
         │                                        │
         │        AWS Batch / EC2 Services        │
         │                                        │
         └────────────────────────────────────────┘
```

This architecture provides:

1. **Separation of Concerns**: Distinct buckets for input data and results
2. **Security**: All buckets block public access by default
3. **Data Protection**: Optional versioning and encryption
4. **Least Privilege Access**: IAM policies grant only necessary permissions
5. **Service Integration**: IAM role designed for EC2 and AWS Batch integration

## Usage

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform v1.0.0 or newer

### Configuration

Edit the `variables.tf` file to customize:

- AWS region
- Environment name
- Project name
- Bucket name prefixes
- Enable/disable versioning
- Enable/disable encryption

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

- Bucket IDs and ARNs for both data and results buckets
- IAM role ARN and name
- IAM policy ARN

These can be used in subsequent Terraform configurations for deploying compute resources that need to access these buckets.

## Security Considerations

- All buckets have public access blocked by default
- The IAM role follows the principle of least privilege
- Data bucket is configured for read-only access
- Results bucket allows read/write access
- Consider enabling encryption for sensitive data
- Consider enabling versioning for data integrity

## Future Enhancements

- Implement lifecycle policies for cost optimization
- Add CORS configuration for web application access
- Configure bucket logging for audit trails
- Set up event notifications for workflow automation
- Implement S3 inventory for large-scale data management
- Create VPC endpoints for secure access from VPC resources