locals {
  domain_parts = split(".", var.domain_name)
  domain_parts_len = length(local.domain_parts)

  # Extract the root domain from var.domain_name
  root_domain = join(".", slice(local.domain_parts, local.domain_parts_len - 2, local.domain_parts_len))
}

data "aws_route53_zone" "main" {
  name         = local.root_domain
}

resource "aws_route53_record" "static_website_alias" {
    zone_id = data.aws_route53_zone.main.zone_id
    name = var.domain_name
    type = "A"
    alias {
        name = aws_cloudfront_distribution.cloudfront.domain_name
        zone_id = aws_cloudfront_distribution.cloudfront.hosted_zone_id
        evaluate_target_health = false
    }
}

resource "aws_route53_record" "static_website_cert_validation_record" {
    for_each = {
        for dvo in aws_acm_certificate.static_website_cert.domain_validation_options: dvo.domain_name => {
            name   = dvo.resource_record_name
            record = dvo.resource_record_value
            type   = dvo.resource_record_type
        }
    }
    allow_overwrite = true
    name            = each.value.name
    records         = [each.value.record]
    ttl             = 60
    type            = each.value.type
    zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "static_website_cert_validation" {

  certificate_arn = aws_acm_certificate.static_website_cert.arn

  validation_record_fqdns = [
    for record in aws_route53_record.static_website_cert_validation_record : record.fqdn
  ]

  depends_on = [
    aws_route53_record.static_website_cert_validation_record,
  ]
}