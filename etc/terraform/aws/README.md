# Terraform for Testing in AWS

This Terraform project generates a key pair locally, builds a security group and EC2 instance, and provides utilities
to make building this relatively easy using a Makefile.

## Variables

There are a few variables that must be defined for Terraform actions to work when using the Makefile:

 - `REGION`: if you're not in `us-east-1`, pass this value to set your region.
 - `SSH_METHOD`: by default, we use the private IP to shell into the host, set to `public` to use the _public_ IP.
 - `SUBNET_ID`: a subnet id to launch the instance into.
 - `VPC_ID`: a VPC id to launch the instance into.

Example:

```shell
make -sC etc/terraform/aws VPC_ID=vpc-deadbeef SUBNET_ID=subnet-deadbeefcafebabe plan
```
