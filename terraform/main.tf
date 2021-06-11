resource "aws_instance" "verifyInstance" {
  ami           = "ami-0d2fb06f3c1484132"
  instance_type = "t2.small"
  user_data     = <<-EOF
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

output "DNS" {
  value = aws_instance.verifyInstance.public_dns
}

output "INSTANCE_ID" {
  value = aws_instance.verifyInstance.id
}

output "AVAILABILITY_ZONE" {
  value = aws_instance.verifyInstance.availability_zone
}
