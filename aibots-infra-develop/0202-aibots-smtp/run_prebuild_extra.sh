echo "[run_prebuild_extra INFO] Going to terraform taint aws_iam_access_key"
# Removing ECR and KMS from state file
for resource in $(terraform state list | grep -e 'aws_iam_access_key\.')
do
  echo "tainting $resource"
  terraform taint $resource
done
