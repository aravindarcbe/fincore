# Hosting FinCore on AWS

Provisions one small EC2 server that runs the whole app (FastAPI backend +
built React frontend, both behind nginx) for `aravindarcbe.com`. This
matches the app's own design note (see the root `README.md`): SQLite on a
single instance needs no rewrite and is the right fit for a personal,
single-user app.

**Nobody but you ever needs your AWS keys or SSH private key** - not this
repo, not Claude. You run the first `terraform apply` yourself, from your
own machine, using your own credentials. After that one-time bootstrap,
GitHub Actions takes over using short-lived OIDC tokens - no long-lived
keys stored anywhere, ever.

## What gets created

- 1 EC2 instance (`t3.micro` by default - check the Free Tier page in your
  AWS console for which size your account gets free)
- 1 security group (80/443 open to everyone, 22 open only to your IP, for
  your own manual access - CI never uses SSH)
- 1 Elastic IP (a fixed public IP for the instance)
- 1 IAM role + instance profile so AWS Systems Manager can reach the
  instance (this is how GitHub Actions triggers deploys - see below)
- 2 IAM roles GitHub Actions can assume via OIDC: one scoped to managing
  this stack's infrastructure, one scoped to only sending a deploy command
  to this one instance
- Optionally, a Route53 hosted zone (only if you set `manage_dns_zone = true`)

Nothing else - no load balancer, no NAT gateway, no RDS.

## Why SSM instead of SSH for deploys

GitHub-hosted runners don't have a fixed IP address, so there's no CIDR you
could add to the security group to let them SSH in. AWS Systems Manager
Run Command sidesteps this entirely: the instance polls out to AWS (no
inbound port needed for it), and GitHub Actions asks AWS to run a command
on it, authenticated via IAM instead of a key. Port 22 stays locked to your
own IP, for your own manual access.

## One-time setup (on your own machine)

1. **Install the tools**: [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
   and [Terraform](https://developer.hashicorp.com/terraform/install) (>= 1.5).

2. **Create an IAM user for yourself** in the AWS Console (IAM → Users →
   Create user) with programmatic access. Attach:
   - `AmazonEC2FullAccess`
   - `AmazonRoute53FullAccess` (only needed if you'll set `manage_dns_zone = true`)
   - `IAMFullAccess` (needed just for this first apply, since it creates the
     OIDC provider and the two GitHub Actions roles described above - see
     `oidc.tf` if you'd rather hand-scope this instead)
   - `AmazonS3FullAccess` (for the remote state bucket)

   Generate an access key for that user (IAM → your user → Security
   credentials → Create access key → Command Line Interface (CLI)), then:
   ```
   aws configure
   ```
   This stores your credentials locally in `~/.aws/credentials` - they
   never leave your machine.

3. **Generate an SSH key pair** if you don't already have one (for your own
   manual access - not used by CI):
   ```
   ssh-keygen -t ed25519 -C "fincore-server" -f ~/.ssh/fincore_ed25519
   ```

4. **Find your current public IP** (for locking down SSH):
   ```
   curl -s https://checkip.amazonaws.com
   ```

5. **Bootstrap remote state** - see `../terraform-bootstrap/README.md`:
   ```
   cd infra/terraform-bootstrap
   terraform init && terraform apply
   terraform output backend_hcl
   ```
   Copy that output into `infra/terraform/backend.hcl` (copy
   `backend.hcl.example` first).

6. **Configure your variables**:
   ```
   cd infra/terraform
   cp terraform.tfvars.example terraform.tfvars
   export TF_VAR_ssh_public_key="$(cat ~/.ssh/fincore_ed25519.pub)"
   ```
   Edit `terraform.tfvars` and fill in:
   - `allowed_ssh_cidr` → your IP from step 4, with `/32`, e.g. `"203.0.113.5/32"`
   - `letsencrypt_email` → your email (for cert expiry notices)

   `terraform.tfvars` and `backend.hcl` are both gitignored.

## Provision the server (first time - run locally)

```
cd infra/terraform
terraform init -backend-config=backend.hcl
terraform plan     # review what it's about to create
terraform apply    # type yes when it asks
```

This also creates the two GitHub Actions IAM roles (`oidc.tf`) - this is
the one time something has to already be trusted in AWS before GitHub can
be trusted too. Every apply after this one can run from GitHub Actions
instead.

Watch the bootstrap script finish:
```
ssh ubuntu@<server_public_ip> 'tail -f /var/log/fincore-bootstrap.log'
```

Terraform's `next_steps` output lists everything below, plus the exact
GitHub Actions **variables** to add (Settings → Secrets and variables →
Actions → *Variables* tab - not Secrets, since none of this is sensitive:
OIDC means no AWS keys, SSM means no SSH keys, and a public key isn't
secret either).

## Point your domain at it

- **If you're managing DNS at your registrar** (this is the default here,
  `manage_dns_zone = false`): add two `A` records at your registrar
  pointing at `server_public_ip`:
  - `@` (root domain) → `server_public_ip`
  - `www` → `server_public_ip`

- **If you'd rather have Route53 manage DNS**: set `manage_dns_zone = true`
  and re-apply. It prints `route53_name_servers` - update your registrar's
  nameservers to those. Costs Route53's ~$0.50/month hosted-zone fee.

Check propagation: `dig +short aravindarcbe.com`.

## Get HTTPS working

Once DNS resolves, SSH in and run the command from `next_steps`:

```
ssh ubuntu@<server_public_ip>
sudo certbot --nginx -d aravindarcbe.com -d www.aravindarcbe.com \
  -m you@example.com --agree-tos --redirect -n
```

Manual, one-time - Let's Encrypt needs DNS already pointing at the server
first, so it can't be part of the automated bootstrap. Certbot sets up its
own renewal timer after this.

## From here on: everything is `git push`

Once the GitHub Actions variables from `next_steps` are set:

- Push/merge app code to `main` → `.github/workflows/deploy.yml` redeploys
  the app via SSM.
- Push/merge changes under `infra/terraform/` to `main` →
  `.github/workflows/terraform.yml` applies them automatically. Pull
  requests touching that path get a `terraform plan` in the Actions log
  first, so you can review before merging.

No more local `terraform`/`aws` commands needed for routine work. Keep your
local IAM user and this module's local knowledge around anyway as a
fallback in case either GitHub Actions role ever needs fixing by hand.

## State locking

There's no DynamoDB lock table backing the S3 state - for a single-person
project, two applies running at the exact same moment is unlikely enough
that the extra moving part isn't worth it. The GitHub Actions `terraform`
workflow uses a single job per event, and pushes to `main` are naturally
serial, so in practice concurrent applies would only happen if you run a
local `terraform apply` at the exact moment a push to main is being
applied by CI. Just avoid doing both at once. (Terraform 1.10+ supports
native S3 locking via `use_lockfile = true` if you upgrade later and want
this fully covered.)

## Updating the server manually

```
ssh ubuntu@<server_public_ip>
sudo /opt/fincore/deploy.sh
```
Pulls the latest `main`, rebuilds the frontend, restarts the backend. This
is exactly what the GitHub Actions deploy workflow triggers remotely.

## Tearing it down

```
terraform destroy
```
Deletes the instance, security group, Elastic IP, IAM roles, and Route53
zone (if created). It does **not** delete the state bucket from
`terraform-bootstrap` - destroy that separately if you're done for good:
```
cd ../terraform-bootstrap && terraform destroy
```

An allocated-but-unattached Elastic IP and EBS storage keep billing even
when the instance is stopped, so prefer `destroy` over just stopping the
instance if you're done with it for a while.

## Cost awareness

Free Tier (first 12 months on a new AWS account) typically covers:
- 750 hrs/month of a `t2.micro` or `t3.micro` instance (one instance
  running 24/7 fits inside this)
- 30GB of EBS storage
- S3 storage for state is a few KB - effectively free
- Route53 is **not** part of Free Tier - ~$0.50/month per hosted zone if
  you enable `manage_dns_zone`

After 12 months, a `t3.micro` running 24/7 costs roughly $7-9/month
depending on region. Set a
[budget alert](https://console.aws.amazon.com/billing/home#/budgets) in
the AWS console so you're notified before anything unexpected is charged.

## Your data

The SQLite database and uploaded documents live on the instance's own disk
at `/opt/fincore/backend/data/`. They are **not** backed up automatically.
Periodically download a copy:
```
scp ubuntu@<server_public_ip>:/opt/fincore/backend/data/fincore.db ./backup-fincore.db
```
or take an EBS snapshot from the AWS Console before any risky change.
