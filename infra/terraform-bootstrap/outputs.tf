output "state_bucket_name" {
  value = aws_s3_bucket.tf_state.bucket
}

output "backend_hcl" {
  description = "Paste this into infra/terraform/backend.hcl"
  value       = <<-EOT
    bucket = "${aws_s3_bucket.tf_state.bucket}"
    key    = "fincore/terraform.tfstate"
    region = "${var.aws_region}"
    encrypt = true
  EOT
}
