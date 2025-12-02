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

. ../../../login.$login_path.sh

# Single file to deploy dev, uat or prd. the env has to be passed as param to the script

echo '[INFO] Starting Deploy Script...'

function check_environment(){
    echo '[INFO] Checking Environment Parameter provided...'
    echo "[INFO] Environment Passed is '$1'"
    # if [ "$1" != "nick" ]  &&   [ "$1" != "wilson" ]  &&  [ "$1" != "yijing" ]; then
    if [ "$1" != "poc" ]; then
        echo '[ERROR] INVALID ENVIRONMENT. Expected nick, wilson or yijing.'
        echo FAIL
        exit 1
    else
        export ENV=$1
        echo '[INFO] VALID ENVIRONMENT'
        echo [INFO] OK
    fi
}

check_environment $1
proj=${original_working_directory##*/}


echo
echo "[INFO] Aligning these baseline data files..."
for FILE in data.baseline.*; do
  if [ ! -e $FILE ]; then
    echo "no files";
    continue;
  fi
  echo "copying >>" $FILE;
  cp -pr ../../$FILE $FILE;
done

echo
echo "[INFO] Aligning main_backend.tf files..."
  cp -pr ../main_backend.tf .;

echo
echo "[INFO] Aligning these layer data files..."
for FILE in data.[0-9][0-9][0-9][0-9]-*; do
  if [ ! -e $FILE ]; then
    echo "no files";
    continue;
  fi
  echo "copying >>" $FILE;
  cp -pr ../data/$FILE $FILE;
done


echo "[INFO] Original Working Directory is $original_working_directory"

if [ -d "source/lambda" ]; then
  # Take action if $DIR exists. #
  echo 'Running prebuild.sh...'
  ./run_prebuild.sh
  echo 'Finished prebuild.sh'
fi

echo
# Just to make sure we come back to this working directory because the prebuild.sh may can to some other path.
echo "[INFO] Returning to $original_working_directory..."
cd $original_working_directory
echo
echo '[INFO] Going to run terraform for project: '$proj
echo
echo '---------------Terraform Region---------------'
echo
echo '[INFO] Initializing Terraform'
# terraform init -backend-config="./environments/gvt_backend.tf" -backend-config="key=$proj/terraform.tfstate" -backend-config="region=ap-southeast-1"
terraform init -backend-config="key=$proj/terraform.tfstate"
echo '[INFO] Terraform initialized'
echo
echo "[INFO] Creating Workspace - $1"
terraform workspace new $1
echo
echo "[INFO] Created and switched to workspace - $1"
terraform workspace select $1
echo
echo '[INFO] Applying Terraform'
# Check if environments directory exist
if [ -d "environments" ]; then
  # Take action if $DIR exists. #
  echo "[INFO] with environments parameters"
  terraform apply $2 \
  -var-file="./environments/gvt_proj_$1.tfvars"
else
  terraform apply $2
fi

echo
echo '[INFO] All Done'
echo
date
















