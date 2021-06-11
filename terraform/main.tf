resource "aws_instance" "verifyInstance" {
  ami                  = "ami-0d2fb06f3c1484132"
  instance_type        = "t2.small"
  iam_instance_profile = aws_iam_instance_profile.verify_profile.name
  user_data            = <<-EOF
                        #!/bin/bash
                        sudo su
                        amazon-linux-extras install docker
                        service docker start
                        usermod -a -G docker ec2-user
                        chkconfig docker on
                        yum install -y git vim
                        curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
                        chmod +x /usr/local/bin/docker-compose

                        su ec2-user git clone https://github.com/jordanbertasso/MACS-Verify.git ~/discord-verify

                        reboot
                  EOF
}

resource "aws_iam_role" "ses_role" {
  name                = "SES"
  managed_policy_arns = ["arn:aws:iam::aws:policy/AmazonSESFullAccess"]
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_instance_profile" "verify_profile" {
  name = "verify_profile"
  role = aws_iam_role.ses_role.name
}
