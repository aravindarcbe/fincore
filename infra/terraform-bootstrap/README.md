# Terraform state bootstrap

A tiny, separate Terraform config that creates one thing: the S3 bucket
that `infra/terraform`'s state lives in. It exists so both your laptop and
GitHub Actions can share the same view of what's been provisioned.

You apply this **once**, locally, and essentially never touch it again.
It can't bootstrap itself into `infra/terraform`'s remote state (that
bucket doesn't exist yet at this point) - that's why it's its own module
with its own local state file.

```
cd infra/terraform-bootstrap
terraform init
terraform apply
terraform output backend_hcl
```

Copy that `backend_hcl` output into `infra/terraform/backend.hcl` (see
`backend.hcl.example` there), then continue with `infra/terraform/README.md`.

Keep this module's own `terraform.tfstate` file safe (it's local, on your
machine, gitignored) - it's the only record of which S3 bucket is "the"
state bucket. If you ever lose it, the bucket still exists in AWS; you'd
just need to `terraform import` it back in, or point `infra/terraform`'s
backend at it directly since the bucket name is stable.
