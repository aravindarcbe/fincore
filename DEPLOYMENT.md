# Deploying FinCore to production (aravindarcbe.com)

Two parts:
1. **Infrastructure** (Terraform, one-time, run manually by you) - provisions
   the AWS server. See [`infra/terraform/README.md`](infra/terraform/README.md)
   for the full step-by-step.
2. **App deployment** (GitHub Actions, automatic) - every push to `main`
   redeploys the latest code onto that server. Set up once below.

Nobody but you ever handles your AWS keys or SSH private key - you run
Terraform yourself locally, and you're the one who pastes the GitHub
secrets in step 2 below (Claude/this repo never sees them).

## Git workflow

`main` is production. Merging a PR into `main` (or pushing to it directly)
triggers [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml),
which SSHes into the server and runs its `deploy.sh` (git pull, rebuild
frontend, restart the backend service). Feature branches and PRs don't
deploy anything on their own - only `main` does.

Recommended flow:
```
git checkout -b my-change
# ... work, commit ...
git push -u origin my-change
# open a PR into main, review, merge
# -> main updates -> deploy.yml runs automatically -> aravindarcbe.com updates
```

## One-time setup: connect GitHub Actions to your server

After you've run `terraform apply` (see the infra README) and have a
`server_public_ip`:

1. On GitHub: repo → **Settings** → **Environments** → **New environment**
   → name it `production`. (Optional but recommended: under this
   environment, add yourself as a **required reviewer** so every deploy
   needs a manual click-to-approve before it runs - a nice safety net for a
   personal-finance app.)

2. Still under that `production` environment (or under **Settings** →
   **Secrets and variables** → **Actions** if you skipped step 1's
   environment), add three secrets:

   | Secret | Value |
   |---|---|
   | `EC2_HOST` | the `server_public_ip` Terraform printed |
   | `EC2_USER` | `ubuntu` |
   | `EC2_SSH_KEY` | the contents of your **private** key file (e.g. `cat ~/.ssh/fincore_ed25519`) - the one whose `.pub` half you gave Terraform |

3. Push (or merge a PR) to `main`. Check the **Actions** tab - you should
   see "Deploy to production" run and finish green. Visit
   `https://aravindarcbe.com` to confirm.

You can also trigger a deploy manually anytime from the Actions tab
("Deploy to production" → **Run workflow**) without needing a new commit.

## What doesn't auto-deploy

Changes to the Terraform files under `infra/terraform/` are **not** applied
automatically - infrastructure changes are rare and risky enough that you
should run `terraform plan` / `terraform apply` yourself and read the diff
before applying. See the infra README for that flow.
