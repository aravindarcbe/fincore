output "server_public_ip" {
  description = "The server's fixed public IP. Point your domain's DNS A record here."
  value       = aws_eip.fincore.public_ip
}

output "ssh_command" {
  description = "Command to SSH into the server (uses the private half of the key you pointed ssh_public_key_path at)."
  value       = "ssh ubuntu@${aws_eip.fincore.public_ip}"
}

output "route53_name_servers" {
  description = "Only set if manage_dns_zone = true - update these at your domain registrar."
  value       = var.manage_dns_zone ? aws_route53_zone.fincore[0].name_servers : []
}

output "next_steps" {
  value = <<-EOT
    1. Point your domain's DNS A record (both "${var.domain_name}" and "www.${var.domain_name}") at ${aws_eip.fincore.public_ip}
       - if manage_dns_zone=true, instead update your registrar's nameservers to route53_name_servers above.
    2. Wait for DNS to propagate (check: dig +short ${var.domain_name})
    3. SSH in and issue the TLS certificate:
       ssh ubuntu@${aws_eip.fincore.public_ip}
       sudo certbot --nginx -d ${var.domain_name} -d www.${var.domain_name} -m ${var.letsencrypt_email} --agree-tos --redirect -n
    4. Visit https://${var.domain_name}
  EOT
}
