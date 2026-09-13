terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Shared state in S3 so both your local machine and GitHub Actions see the
  # same infrastructure. The bucket comes from infra/terraform-bootstrap
  # (applied once, separately - see that module's README). Partial config:
  # run `terraform init -backend-config=backend.hcl` (see backend.hcl.example).
  #
  # No DynamoDB lock table - see README.md's "State locking" note for why
  # that's an acceptable tradeoff here, and what to do instead if two
  # applies ever run at the same time.
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}
