# AWS EC2 Instance for Testing

provider "aws" {
  region = "${var.region}"
}

variable "allowed_cidr_ranges" {
  type = "list"
  default = ["10.0.0.0/8", "192.168.0.0/16"]
}

variable "region" { default = "us-east-1" }
variable "ssh_public_key" {}
variable "subnet_id" {}
variable "vpc_id" {}

data "aws_ami" "coreos_stable" {
  most_recent = "true"

  filter {
    name = "name"
    values = ["CoreOS-stable-*-hvm"]
  }

  filter {
    name = "virtualization-type"
    values = ["hvm"]
  }

  # coreos
  owners = ["595879546273"]
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/templates/cloud-config.yml.tpl")}"

  vars = {
    hostname = "metascrape-aws-tester-${random_string.id.result}"
  }
}

resource "random_string" "id" {
  length = 8
  upper = false
  lower = true
  number = true
  special = false
}

resource "aws_key_pair" "default" {
  key_name = "metascrape-aws-tester-${random_string.id.result}"
  public_key = "${var.ssh_public_key}"
}

resource "aws_instance" "default" {
  ami = "${data.aws_ami.coreos_stable.id}"
  instance_initiated_shutdown_behavior = "terminate"
  instance_type = "t2.micro"
  key_name = "${aws_key_pair.default.id}"
  vpc_security_group_ids = ["${aws_security_group.default.id}"]
  subnet_id = "${var.subnet_id}"

  user_data = "${data.template_file.cloud_init.rendered}"

  credit_specification {
    cpu_credits = "unlimited"
  }

  tags = {
    Name = "metascrape-aws-tester-${random_string.id.result}"
  }
}

resource "aws_security_group" "default" {
  name = "metascrape-aws-tester-${random_string.id.result}"
  description = "Temporary security group for testing metascrape."
  vpc_id = "${var.vpc_id}"
}

resource "aws_security_group_rule" "ingress_ssh" {
  type = "ingress"
  from_port = 22
  to_port = 22
  protocol = "tcp"
  cidr_blocks = "${var.allowed_cidr_ranges}"

  security_group_id = "${aws_security_group.default.id}"
}

resource "aws_security_group_rule" "ingress_icmp" {
  type = "ingress"
  from_port = -1
  to_port = -1
  protocol = "icmp"
  cidr_blocks = "${var.allowed_cidr_ranges}"

  security_group_id = "${aws_security_group.default.id}"
}

resource "aws_security_group_rule" "egress" {
  type = "egress"
  from_port = 0
  to_port = 65535
  protocol = "all"
  cidr_blocks = ["0.0.0.0/0"]

  security_group_id = "${aws_security_group.default.id}"
}

output "instance_id" { value = "${aws_instance.default.id}" }
output "private_ip" { value = "${aws_instance.default.private_ip}" }
output "public_ip" { value = "${aws_instance.default.public_ip}" }
output "security_group_id" { value = "${aws_security_group.default.id}" }
output "ssh_user" { value = "core" }
