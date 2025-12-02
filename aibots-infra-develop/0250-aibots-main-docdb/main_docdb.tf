resource "aws_docdbelastic_cluster" "project" {
  # we will ignore password change, else see below on the steps to align the change.
  # with this, you will just change the password from the console.
  lifecycle {
    ignore_changes = [ admin_user_password ]
  }

  admin_user_name = "${var.project_code}Admin"
  admin_user_password = random_password.project[0].result
  # changing the password is a painful process, you need to
  # > terrafrom rm random_password.project # to remove the random_password
  # > ./run.sh apply uat # to generate the new random_password.project
  # > get the new string from secret
  # > download the state file from S3
  # > edit the state file
  # > upload the edit state file back to S3
  # > change the Metadata of the uploaded state file to application/json
  auth_type = "PLAIN_TEXT" # use this, because SECRET_ARN does not work.
  name = "${local.docdb_name}"
  preferred_maintenance_window = "Sun:20:00-Sun:20:40"
  shard_capacity = 2
  shard_count = 1
  # needs 2 or more subnets
  subnet_ids = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  vpc_security_group_ids = [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  tags = local.tags
}