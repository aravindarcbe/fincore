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
  public_key = file(var.ssh_public_key_path)
}

resource "aws_instance" "fincore" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  key_name               = aws_key_pair.fincore.key_name
  vpc_security_group_ids = [aws_security_group.fincore_web.id]

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
