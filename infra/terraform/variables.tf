variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1" # Mumbai
}

variable "domain_name" {
  description = "Your registered domain, e.g. aravindarcbe.com (no protocol, no trailing dot)."
  type        = string
  default     = "aravindarcbe.com"
}

variable "manage_dns_zone" {
  description = <<-EOT
    If true, Terraform creates a Route53 hosted zone for domain_name and A
    records pointing at the server. You'd then update your domain
    registrar's nameservers to the ones Route53 gives you.
    If false (default), Terraform only outputs the server's IP - you add an
    A record for the domain yourself in whatever DNS panel your registrar
    already gives you. False is simpler and avoids Route53's ~$0.50/month
    hosted-zone fee, and is the recommended option unless you specifically
    want AWS managing your DNS.
  EOT
  type        = bool
  default     = false
}

variable "instance_type" {
  description = "EC2 instance type. t3.micro/t2.micro are AWS Free Tier eligible for 12 months on new accounts - check the Free Tier page in your AWS console to confirm which one applies to your account."
  type        = string
  default     = "t3.micro"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GB (Free Tier covers up to 30GB of gp3/gp2 per month)."
  type        = number
  default     = 20
}

variable "ssh_public_key_path" {
  description = "Path to YOUR OWN local SSH public key file (e.g. ~/.ssh/id_ed25519.pub), generated on your machine. Never your private key - Terraform only ever needs the public half."
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH into the box, e.g. \"203.0.113.5/32\" (your current public IP). Never leave this as 0.0.0.0/0."
  type        = string
}

variable "github_repo_url" {
  description = "Git URL the server clones/pulls the app from."
  type        = string
  default     = "https://github.com/aravindarcbe/fincore.git"
}

variable "git_branch" {
  description = "Branch the server deploys from - this should be your production branch (main)."
  type        = string
  default     = "main"
}

variable "letsencrypt_email" {
  description = "Email used for Let's Encrypt certificate expiry notices (used manually with certbot after DNS is live - see README)."
  type        = string
}
