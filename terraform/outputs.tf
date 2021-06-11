output "DNS" {
  value = aws_instance.verifyInstance.public_dns
}

output "INSTANCE_ID" {
  value = aws_instance.verifyInstance.id
}

output "AVAILABILITY_ZONE" {
  value = aws_instance.verifyInstance.availability_zone
}