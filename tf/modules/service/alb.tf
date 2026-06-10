locals {
  domain_parts = split(".", var.domain_name)
  subdomain    = local.domain_parts[0]
}

resource "aws_alb" "main" {
    name        = "${local.subdomain}-load-balancer"
    subnets         = aws_subnet.public.*.id
    security_groups = [aws_security_group.lb.id]
}

resource "aws_alb_target_group" "api" {
    name        = "${local.subdomain}-target-group"
    port        = 8000
    protocol    = "HTTP"
    vpc_id      = aws_vpc.main.id
    target_type = "ip"

    health_check {
        healthy_threshold   = "3"
        interval            = "30"
        protocol            = "HTTP"
        matcher             = "200"
        timeout             = "3"
        path                = var.health_check_path
        unhealthy_threshold = "2"
    }
}


# Redirect all traffic from the ALB to the target group
resource "aws_alb_listener" "front_end" {
  load_balancer_arn = aws_alb.main.id
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate.service_cert.arn
  depends_on        = [aws_acm_certificate_validation.service_cert_validation]

  default_action {
    target_group_arn = aws_alb_target_group.api.id
    type             = "forward"
  }
}
