# Hosting FinCore on AWS

Provisions one small EC2 server that runs the whole app (FastAPI backend +
built React frontend, both behind nginx) for `aravindarcbe.com`. This
matches the app's own design note (see the root `README.md`): SQLite on a
single instance needs no rewrite and is the right fit for a personal,
single-user app.

**Nobody but you ever needs your AWS keys or SSH private key** - not this
repo, not Claude. You run every `terraform`/`aws` command yourself, from
your own machine, using your own credentials.

## What gets created

- 1 EC2 instance (`t3.micro` by default - check the Free Tier page in your
  AWS console for which size your account gets free)
- 1 security group (80/443 open to everyone, 22 open only to your IP)
- 1 Elastic IP (a fixed public IP for the instance, so DNS doesn't break on
  reboot)
- Optionally, a Route53 hosted zone (only if you set `manage_dns_zone = true`)

Nothing else - no load balancer, no NAT gateway, no RDS. Those all cost
money this project doesn't need.

## One-time setup (on your own machine)

1. **Install the tools**: [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
   and [Terraform](https://developer.hashicorp.com/terraform/install) (>= 1.5).

2. **Create an IAM user for yourself** in the AWS Console (IAM → Users →
   Create user) with programmatic access. Attach these AWS managed policies
   (broad but scoped to just the services this uses):
   - `AmazonEC2FullAccess`
   - `AmazonRoute53FullAccess` (only needed if you'll set `manage_dns_zone = true`)

   Generate an access key for that user (IAM → your user → Security
   credentials → Create access key), then on your machine run:
   ```
   aws configure
   ```
   and paste the access key / secret when prompted. This stores your
   credentials locally in `~/.aws/credentials` - they never leave your
   machine and are never shared with anyone else, including Claude.

3. **Generate an SSH key pair** if you don't already have one:
   ```
   ssh-keygen -t ed25519 -C "fincore-server" -f ~/.ssh/fincore_ed25519
   ```
   This creates `~/.ssh/fincore_ed25519` (private, keep it secret) and
   `~/.ssh/fincore_ed25519.pub` (public, safe to share - Terraform only
   ever reads this one).

4. **Find your current public IP** (for locking down SSH):
   ```
   curl -s https://checkip.amazonaws.com
   ```

5. **Configure your variables**:
   ```
   cd infra/terraform
   cp terraform.tfvars.example terraform.tfvars
   ```
   Edit `terraform.tfvars` and fill in:
   - `ssh_public_key_path` → path to the `.pub` file from step 3
   - `allowed_ssh_cidr` → your IP from step 4, with `/32`, e.g. `"203.0.113.5/32"`
   - `letsencrypt_email` → your email (for cert expiry notices)

   `terraform.tfvars` is gitignored - it stays on your machine only.

## Provision the server

```
cd infra/terraform
terraform init
terraform plan     # review what it's about to create
terraform apply    # type yes when it asks
```

This takes a couple of minutes for AWS to launch the instance, plus a few
more minutes in the background for the bootstrap script (installs nginx,
Python, Node, clones the repo, builds the frontend, starts the backend).
You can watch it finish with:
```
ssh ubuntu@<server_public_ip> 'tail -f /var/log/fincore-bootstrap.log'
```
(Ctrl+C once you see "FinCore bootstrap finished".)

Terraform prints a `next_steps` output at the end with the exact commands
for what follows.

## Point your domain at it

- **If you're managing DNS at your registrar** (GoDaddy, Namecheap, wherever
  you bought `aravindarcbe.com`) - the simplest path, and the default here
  (`manage_dns_zone = false`): log into your registrar's DNS panel and add
  two `A` records, both pointing at the `server_public_ip` Terraform
  printed:
  - `@` (root domain) → `server_public_ip`
  - `www` → `server_public_ip`

- **If you'd rather have Route53 manage DNS**: set `manage_dns_zone = true`
  in `terraform.tfvars` and re-run `terraform apply`. It creates a hosted
  zone and prints `route53_name_servers` - update your registrar's
  nameserver settings to those 4 values. This costs Route53's small hosted
  zone fee (~$0.50/month) on top of the free tier.

DNS changes can take anywhere from a few minutes to a few hours to
propagate. Check with `dig +short aravindarcbe.com`.

## Get HTTPS working

Once `dig +short aravindarcbe.com` returns your server's IP, SSH in and run
the command from Terraform's `next_steps` output:

```
ssh ubuntu@<server_public_ip>
sudo certbot --nginx -d aravindarcbe.com -d www.aravindarcbe.com \
  -m you@example.com --agree-tos --redirect -n
```

This is a manual, one-time step because Let's Encrypt needs your DNS to
already resolve to the server before it can issue a certificate - it can't
be done as part of the automated bootstrap. Certbot sets up auto-renewal on
its own (a systemd timer), so you only do this once.

Visit `https://aravindarcbe.com` - you should see FinCore.

## Continuous deployment from `main`

See `.github/workflows/deploy.yml` in the repo root - once you add three
GitHub repo secrets (`EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`), every push to
`main` automatically SSHes in and redeploys. See that workflow file's
comments, or the root `DEPLOYMENT.md`, for exact setup steps.

## Updating the server manually

```
ssh ubuntu@<server_public_ip>
sudo /opt/fincore/deploy.sh
```
Pulls the latest `main`, rebuilds the frontend, restarts the backend.

## Changing infrastructure later

Edit the `.tf` files, then `terraform plan` and `terraform apply` again.
Terraform only changes what's different - it won't recreate the whole
server for something like a security group tweak.

## Tearing it down

```
terraform destroy
```
Deletes the instance, security group, and Elastic IP (and Route53 zone, if
you created one). Do this if you stop using the app - a stopped-but-not-
destroyed instance doesn't run, but an allocated Elastic IP still costs a
small hourly fee even when unattached, and EBS storage keeps billing too.

## Cost awareness

Free Tier (first 12 months on a new AWS account) typically covers:
- 750 hrs/month of a `t2.micro` or `t3.micro` instance (one instance running
  24/7 fits inside this)
- 30GB of EBS storage
- Route53 is **not** part of Free Tier - it's a flat ~$0.50/month per
  hosted zone if you enable `manage_dns_zone`

After 12 months, or if you exceed Free Tier limits, a `t3.micro` running
24/7 costs roughly $7-9/month depending on region. Set a
[budget alert](https://console.aws.amazon.com/billing/home#/budgets) in the
AWS console so you're notified before anything unexpected is charged.

## Your data

The SQLite database and uploaded documents live on the instance's own disk
at `/opt/fincore/backend/data/`. They are **not** backed up automatically.
Periodically download a copy:
```
scp ubuntu@<server_public_ip>:/opt/fincore/backend/data/fincore.db ./backup-fincore.db
```
or take an EBS snapshot from the AWS Console (EC2 → Volumes → your volume →
Actions → Create snapshot) before any risky change.
