Terraform scaffolding for provisioning infrastructure (example: AWS)

This folder contains example Terraform configurations to provision:
- An object storage bucket (S3)
- A managed Postgres instance (RDS)

Notes:
- These are example resources for AWS. Adapt provider and resources for other clouds as needed.
- Do NOT run without reviewing and setting secure values for credentials, passwords, and networking.

Quick start (AWS example):

1. Install Terraform (>= 1.0).
2. Configure AWS credentials (environment variables or shared credentials file).
3. Initialize Terraform:

```bash
cd infrastructure
terraform init
```

4. Review the plan and apply:

```bash
terraform plan -out plan.tfplan
terraform apply plan.tfplan
```

Customize variables in `variables.tf` or pass `-var` flags when running `terraform plan`.

Security and production notes:
- Use Terraform state backend (e.g., S3 + DynamoDB) for collaboration and locking.
- Never commit secrets to the repo; use environment variables or secret manager integrations.
- Provision RDS in private subnets and configure appropriate security groups.
