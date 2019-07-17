#!/usr/bin/make -f

SHELL:=$(shell which bash)

SSH_METHOD?=private

ifeq ($(SSH_METHOD),private)
	SSH_HOST_IP_OUTPUT=private_ip
else
	SSH_HOST_IP_OUTPUT=public_ip
endif

REGION?=us-east-1

gen_keys:
	@mkdir -p keys/
	@if [ ! -e keys/ssh ]; then \
		ssh-keygen -b 4096 -t rsa -f keys/ssh -P '' ; \
	fi

validate:
ifndef VPC_ID
	$(error VPC_ID must be set.)
endif
ifndef SUBNET_ID
	$(error SUBNET_ID must be set.)
endif

init:
	@if ! terraform init >/dev/null 2>/dev/null ; then \
		terraform init ; \
	fi

plan: gen_keys validate init
	@terraform plan -var vpc_id=$(VPC_ID) -var subnet_id=$(SUBNET_ID) -var region=$(REGION) \
		-var ssh_public_key="$(shell cat keys/ssh.pub)"

apply: gen_keys validate init
	@terraform apply -auto-approve -var vpc_id=$(VPC_ID) -var subnet_id=$(SUBNET_ID) -var region=$(REGION) \
		-var ssh_public_key="$(shell cat keys/ssh.pub)"

destroy: gen_keys validate init
	@terraform destroy -force -var vpc_id=$(VPC_ID) -var subnet_id=$(SUBNET_ID) -var region=$(REGION) \
		-var ssh_public_key="$(shell cat keys/ssh.pub)"

output: init
	@terraform output

refresh: init
	@terraform refresh

shell:
	@ssh -i keys/ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l $(shell echo "core") \
		$(shell terraform output $(SSH_HOST_IP_OUTPUT))

tunnel:
	@ssh -i keys/ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -L 8080:169.254.169.254:80 \
		-l $(shell echo "core") $(shell terraform output $(SSH_HOST_IP_OUTPUT))
