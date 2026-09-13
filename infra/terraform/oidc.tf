# Lets GitHub Actions authenticate to AWS with short-lived tokens instead of
# long-lived access keys stored as GitHub secrets. Two separate roles, kept
# narrow on purpose:
#   - github_actions_terraform: can create/change/destroy this stack's own
#     AWS resources (ec2, route53, and just enough iam to manage its own
#     OIDC provider/roles/instance-profile). Used only by
#     .github/workflows/terraform.yml.
#   - github_actions_deploy: can only send an SSM Run Command to the one
#     fincore instance - nothing else. Used only by
#     .github/workflows/deploy.yml, on every push to main.
#
# Bootstrapping note: creating these for the first time still needs a real
# AWS identity - nothing can grant GitHub Actions access to AWS before
# something already-trusted in AWS decides to trust it. That first
# `terraform apply` has to run locally with your own IAM user
# (fincore-terraform-deploy). After that, every future infra change or app
# deploy can run entirely from GitHub Actions - keep that local IAM user
# around anyway as a fallback in case either role ever needs fixing by hand.

data "tls_certificate" "github_actions" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github_actions.certificates[0].sha1_fingerprint]
}

locals {
  # Matches any branch/PR/tag in your repo. Fine for a single-collaborator
  # personal project; tighten to "repo:OWNER/REPO:ref:refs/heads/main" if
  # you want only main able to assume these roles.
  github_repo_sub = "repo:${var.github_owner}/${var.github_repo_name}:*"
}

data "aws_iam_policy_document" "github_oidc_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.github_repo_sub]
    }
  }
}

# ---- Role 1: allowed to run `terraform plan`/`apply` for this stack ----

resource "aws_iam_role" "github_actions_terraform" {
  name               = "fincore-github-actions-terraform"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_trust.json
}

resource "aws_iam_role_policy_attachment" "terraform_ec2" {
  role       = aws_iam_role.github_actions_terraform.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_role_policy_attachment" "terraform_route53" {
  role       = aws_iam_role.github_actions_terraform.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRoute53FullAccess"
}

resource "aws_iam_role_policy_attachment" "terraform_state_s3" {
  role       = aws_iam_role.github_actions_terraform.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Scoped down to just this stack's own IAM resources (its OIDC provider,
# its own fincore-* roles/instance-profile) - not full IAM admin.
data "aws_iam_policy_document" "terraform_iam_scope" {
  statement {
    actions = [
      "iam:CreateOpenIDConnectProvider", "iam:GetOpenIDConnectProvider",
      "iam:DeleteOpenIDConnectProvider", "iam:UpdateOpenIDConnectProviderThumbprint",
      "iam:TagOpenIDConnectProvider", "iam:ListOpenIDConnectProviders",
    ]
    resources = ["*"]
  }
  statement {
    actions = [
      "iam:CreateRole", "iam:GetRole", "iam:DeleteRole", "iam:TagRole",
      "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy",
      "iam:AttachRolePolicy", "iam:DetachRolePolicy", "iam:ListAttachedRolePolicies",
      "iam:ListRolePolicies", "iam:ListInstanceProfilesForRole", "iam:PassRole",
    ]
    resources = ["arn:aws:iam::*:role/fincore-*"]
  }
  statement {
    actions = [
      "iam:CreateInstanceProfile", "iam:GetInstanceProfile", "iam:DeleteInstanceProfile",
      "iam:AddRoleToInstanceProfile", "iam:RemoveRoleFromInstanceProfile", "iam:TagInstanceProfile",
    ]
    resources = ["arn:aws:iam::*:instance-profile/fincore-*"]
  }
}

resource "aws_iam_role_policy" "terraform_iam_scope" {
  name   = "iam-scoped"
  role   = aws_iam_role.github_actions_terraform.name
  policy = data.aws_iam_policy_document.terraform_iam_scope.json
}

# ---- Role 2: allowed only to trigger a deploy via SSM on the one instance ----

resource "aws_iam_role" "github_actions_deploy" {
  name               = "fincore-github-actions-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_trust.json
}

data "aws_iam_policy_document" "deploy_ssm_scope" {
  statement {
    actions = ["ssm:SendCommand"]
    resources = [
      aws_instance.fincore.arn,
      "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript",
    ]
  }
  statement {
    # These two don't support resource-level restriction in IAM.
    actions   = ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "deploy_ssm_scope" {
  name   = "ssm-deploy-scoped"
  role   = aws_iam_role.github_actions_deploy.name
  policy = data.aws_iam_policy_document.deploy_ssm_scope.json
}
