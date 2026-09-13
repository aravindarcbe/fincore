terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local state by default - fine for a single-person project run from one
  # machine. If more than one person/machine will run terraform, switch this
  # to an S3 backend instead so state isn't only on one laptop.
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}
