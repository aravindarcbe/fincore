# Optional - only used if you set manage_dns_zone = true in your tfvars.
# Otherwise leave your domain's DNS wherever it already is and just add an
# A record yourself pointing at the eip output below.

resource "aws_route53_zone" "fincore" {
  count = var.manage_dns_zone ? 1 : 0
  name  = var.domain_name
}

resource "aws_route53_record" "root" {
  count   = var.manage_dns_zone ? 1 : 0
  zone_id = aws_route53_zone.fincore[0].zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.fincore.public_ip]
}

resource "aws_route53_record" "www" {
  count   = var.manage_dns_zone ? 1 : 0
  zone_id = aws_route53_zone.fincore[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = [aws_eip.fincore.public_ip]
}
