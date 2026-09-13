# Deploying FinCore to production (aravindarcbe.com)

Two parts:
1. **Infrastructure** (Terraform) - provisions the AWS server. The very
   first apply runs locally, by you; after that, GitHub Actions applies
   further infra changes automatically. See
   [`infra/terraform/README.md`](infra/terraform/README.md) for the full
   step-by-step, and [`infra/terraform-bootstrap/README.md`](infra/terraform-bootstrap/README.md)
   for the tiny one-time state-bucket setup that comes first.
2. **App deployment** (GitHub Actions) - every push to `main` redeploys the
   latest code onto that server automatically.

Nobody but you ever handles your AWS keys or SSH private key. The first
Terraform apply uses your own local AWS CLI credentials; everything after
that uses OIDC (AWS and GitHub trust each other directly - no stored keys
anywhere) and AWS Systems Manager instead of SSH for deploys. You're the
one who pastes a handful of **non-secret** GitHub Actions *variables* once
(step below) - Claude/this repo never sees or needs them.

## Git workflow

`main` is production. Merging a PR into `main` (or pushing to it directly)
triggers two independent things, each only if relevant files changed:

- [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) - any app
  code change → SSM-deploys onto the server (git pull, rebuild frontend,
  restart the backend service).
- [`.github/workflows/terraform.yml`](.github/workflows/terraform.yml) -
  any change under `infra/terraform/` → applies it. Pull requests touching
  that path get a `terraform plan` posted to the Actions log first.

Feature branches and PRs don't deploy or apply anything on their own -
only `main` does.

Recommended flow:
```
git checkout -b my-change
# ... work, commit ...
git push -u origin my-change
# open a PR into main, review (check the terraform plan if infra changed), merge
# -> main updates -> the relevant workflow(s) run automatically
```

## One-time setup: connect GitHub Actions to AWS

After you've run the **first** `terraform apply` locally (see the infra
README) and have its `next_steps` output in front of you:

1. On GitHub: repo → **Settings** → **Environments** → **New environment**
   → name it `production`. (Optional but recommended: add yourself as a
   **required reviewer** so every deploy/infra-apply needs a manual
   click-to-approve - a nice safety net for a personal-finance app.)

2. Repo → **Settings** → **Secrets and variables** → **Actions** →
   **Variables** tab (not Secrets - nothing here is sensitive) → add:

   | Variable | Value |
   |---|---|
   | `AWS_REGION` | e.g. `ap-south-1` |
   | `EC2_INSTANCE_ID` | from `terraform output instance_id` |
   | `DEPLOY_ROLE_ARN` | from `terraform output github_actions_deploy_role_arn` |
   | `TERRAFORM_ROLE_ARN` | from `terraform output github_actions_terraform_role_arn` |
   | `SSH_PUBLIC_KEY` | the same value you set `ssh_public_key` to |
   | `ALLOWED_SSH_CIDR` | the same value you set `allowed_ssh_cidr` to |
   | `LETSENCRYPT_EMAIL` | the same value you set `letsencrypt_email` to |
   | `TF_BACKEND_HCL` | contents of `infra/terraform/backend.hcl` |

3. Push (or merge a PR) to `main`. Check the **Actions** tab - "Deploy to
   production" should run and finish green. Visit
   `https://aravindarcbe.com` to confirm.

You can also trigger either workflow manually anytime from the Actions tab
(**Run workflow**) without needing a new commit.

## What this buys you

No AWS access keys and no SSH private key live in GitHub at all - OIDC
issues short-lived tokens per run, and deploys go over AWS Systems Manager
instead of SSH. The only things stored in GitHub are non-secret
identifiers (region, instance ID, role ARNs, your public key, your IP,
your email) - if any of them leaked, none grant access to anything on
their own.
