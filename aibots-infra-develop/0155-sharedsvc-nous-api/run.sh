# The login.sh is not in the GIT.
# You will need to figure out how to provide your keypair to the terraform.
# example for the login script:
################################################################################
# export TF_TOKEN_sgts_gitlab__dedicated_com="qeq7EXAMPLE"
# export AWS_ACCESS_KEY_ID="AKIAEXAMPLE"
# export AWS_SECRET_ACCESS_KEY="sJ0mQEXAMPLE"
################################################################################

original_working_directory=$PWD

# see >> https://devhints.io/bash
login_path=${original_working_directory%/*}
login_path=${login_path##*/}

################################################################################
echo
if [ "$1" != "plan" ] && [ "$1" != "apply" ] && [ "$1" != "destroy" ] && [ "$1" != "import" ] && [ "$1" != "fmt" ] && [ "$1" != "refresh" ]; then
  echo '[ERROR] Invalid terraform action. Exiting...'
  exit 1
else
  echo "[INFO] Starting Script to $1"
fi

################################################################################
echo
#  if [ "$2" != "dev" ]  &&   [ "$2" != "uat" ]  &&  [ "$2" != "prod" ] &&  [ "$2" != "mgmt" ]; then
if [ "$2" != "sit" ] && [ "$2" != "prd" ] && [ "$2" != "uat" ] && [ "$2" != "dev" ] && [ "$2" != "poc" ]; then
  echo "[ERROR] Invalid environment $2. Exiting..."
  exit 1
else
  export ENV=$2
  echo "[INFO] $1 environment $2"
fi

################################################################################
echo
echo "[INFO] Login to $2"
. ../login.$2.sh

proj=${original_working_directory##*/}

################################################################################
echo
# just delete the .terraform folder so that terraform will init cleanly, to handle
# switching environment and resequencing the terraform projects
echo "[INFO] removing existing .terraform"
rm -rf .terraform*

proj=${original_working_directory##*/}

################################################################################
echo
echo "[INFO] Aligning these baseline data files..."
for FILE in data.baseline.*.tf; do
  if [ ! -e $FILE ]; then
    echo "no files";
    continue;
  fi
  echo "copying >>" $FILE;
  cp -pr ../data.baseline/$FILE $FILE;
done

################################################################################
echo
echo "[INFO] Aligning backend.env.tf files..."
if [ ! -e ../backend.env/backend.$2.tfvars ]; then
  echo "missing backend config file: ../../infra/backend.env/backend.$2.tfvars";
  exit 1;
else
  echo "copying backend config file: ../../infra/backend.env/backend.$2.tfvars";
  cp -pr ../backend.env/backend.$2.tfvars ./environments/backend.$2.tfvars;
fi

################################################################################
echo
echo "[INFO] Aligning these layer data files..."
for FILE in data.[0-9][0-9][0-9][0-9]-*.tf; do
  if [ ! -e $FILE ]; then
    echo "no files";
    continue;
  fi
  echo "copying >>" $FILE;
  cp -pr ../data/$FILE $FILE;
done

################################################################################
echo
echo "[INFO] Original Working Directory is $original_working_directory"

if [ -d "source/lambda" ]; then
  # Take action if $DIR exists. #
  echo 'Running prebuild.sh...'
  ./run_prebuild.sh
  echo 'Finished prebuild.sh'

  # prebuild will return to relative folder
  # Just to make sure we come back to this working directory
  # in case prebuild may end up in some other path.
  echo "[INFO] Returning to $original_working_directory..."
  cd $original_working_directory
fi

################################################################################
echo
echo "[INFO] Going to run terraform for project: $proj"
echo
echo '[INFO] Initializing Terraform'
terraform init -backend-config="key=$proj/terraform.tfstate" -backend-config="./environments/backend.$2.tfvars"
echo '[INFO] Terraform initialized'

################################################################################
echo
echo "[INFO] Switching to Workspace - $2"
terraform workspace select $2 || terraform workspace new $2

################################################################################
echo
if [ $1 == 'destroy' ]; then
  if [ -e .skip_destroy ]; then
    echo ".skip_destroy found, skipping."
    exit 0
  fi
  echo
  echo "Looking for ECR and KMS in project."
  # Removing ECR and KMS from state file
  for resource in $(terraform state list | grep -e '^aws_ecr_repository' -e '^aws_kms_key')
  do
    read -p "[INPUT] Enter [$resource] to destroy the $resource? : " destroy
    if [[ $destroy == $resource ]]
    then
      echo "$resource will be destroy."
    else
      echo "Keeping $resource."
      terraform state rm $resource
    fi
  done
fi

################################################################################
echo
if [ $1 == 'apply' ]; then
  if [ -e run_prebuild_extra.sh ]; then
    echo "[INFO] Doing extra stuff for this terraform project"
    ./run_prebuild_extra.sh
  fi
fi

################################################################################
echo
echo '[INFO] Terraforming'
# Check if environments directory exist
if [ -e ./environments/project.$2.tfvars ]; then
  # Take action if $DIR exists. #
  echo "[INFO] with environments parameters"
  terraform $1 \
  -var-file="./environments/project.$2.tfvars" $3 $4
else
  terraform $1 $3 $4
fi

exit $?