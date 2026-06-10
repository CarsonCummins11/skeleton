resource "aws_cloudfront_origin_access_control" "current" {
  name                              = "OAC ${aws_s3_bucket.static_website.bucket}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cloudfront" {
    depends_on = [aws_s3_bucket.static_website]
  default_root_object = "index.html"
  enabled = true
  is_ipv6_enabled = true
  aliases = [
    var.domain_name
  ]
  comment         = "${var.domain_name} distribution"
  http_version    = "http2and3"
  price_class     = "PriceClass_100"
  origin {
    domain_name = aws_s3_bucket.static_website.bucket_regional_domain_name
    origin_id = "S3-${aws_s3_bucket.static_website.bucket}"
    origin_access_control_id = aws_cloudfront_origin_access_control.current.id
  }
  custom_error_response {
    error_caching_min_ttl = 3000
    error_code = 404
    response_code = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_caching_min_ttl = 3000
    error_code = 403
    response_code = 200
    response_page_path = "/index.html"
  }
  default_cache_behavior {
    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.static_website.bucket}"
    viewer_protocol_policy = "redirect-to-https"
    min_ttl = 0
    default_ttl = 3600
    max_ttl = 86400
    forwarded_values {
      query_string = true
       cookies {
          forward = "none"
       }
    }
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.static_website_cert.arn
    ssl_support_method = "sni-only"
  }
}
