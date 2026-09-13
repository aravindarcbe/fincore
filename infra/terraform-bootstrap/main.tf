# One-time bootstrap: creates just the S3 bucket that infra/terraform's own
# state will live in. This has to exist *before* infra/terraform can use it
# as a backend, so it's a tiny, separate root module with its own (local)
# state - you apply this once, by hand, and basically never touch it again.
#
# Versioning is on so a bad/corrupted state write can be rolled back to a
# previous version from the S3 console. There's no DynamoDB lock table -
# for a single-person project that's an acceptable tradeoff (see
# infra/terraform/README.md's "State locking" note) rather than another
# moving part to pay for and manage.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "tf_state" {
  bucket = "fincore-terraform-state-${random_id.suffix.hex}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
