data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "fincore" {
  key_name   = "fincore-server"
  public_key = var.ssh_public_key
}

# Lets AWS Systems Manager reach the instance to run the deploy script,
# instead of GitHub Actions needing SSH access (GitHub-hosted runners don't
# have a fixed IP, so they couldn't get through allowed_ssh_cidr anyway).
# SSH stays open only to your own IP, for your own manual access/debugging.
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "fincore_instance" {
  name               = "fincore-instance"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role_policy_attachment" "fincore_instance_ssm" {
  role       = aws_iam_role.fincore_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "fincore_instance" {
  name = "fincore-instance"
  role = aws_iam_role.fincore_instance.name
}

resource "aws_instance" "fincore" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  key_name               = aws_key_pair.fincore.key_name
  vpc_security_group_ids = [aws_security_group.fincore_web.id]
  iam_instance_profile   = aws_iam_instance_profile.fincore_instance.name

  root_block_device {
    volume_size = var.root_volume_size_gb
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    domain_name     = var.domain_name
    github_repo_url = var.github_repo_url
    git_branch      = var.git_branch
  })
  user_data_replace_on_change = true

  tags = {
    Name    = "fincore-server"
    Project = "fincore"
  }
}

resource "aws_eip" "fincore" {
  instance = aws_instance.fincore.id
  domain   = "vpc"

  tags = {
    Name    = "fincore-server"
    Project = "fincore"
  }
}
