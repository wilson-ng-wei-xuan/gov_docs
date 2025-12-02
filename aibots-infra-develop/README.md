# Infra

AIBots infrastructure package manages all AIBots environments (SIT, UAT, PRD in AWS), Azure and eventually GCP 
environments for LLMs

Dependencies:
- Terraform (>v1.9.5)
- Shell

## Structure

AIBots infrastructure package is structured to run as a sequential pipeline, where each step of the pipeline is 
a modular package encapsulated as a folder. The folders are organised in running sequence order indicating the 
sequence of execution. Each modular package generates a set of pre-defined outputs which are stored in the 
`/data` folder. If the data is required in a dependent package, a copy of this data output is stored in the
within the module itself and synced during execution.

Each modular package contains the following:
- A series of `*.tf` files that are executed
- An environment folder containing environment specific configurations, stored as `*.$env.tfvars`

The following file are shared (refactoring-in-progress)
- A `run.sh` script that executes the package
    1. First it performs validation on the inputs i.e. the command should be a valid terraform 
      command and the environment should be a valid environment prefix
    2. Then it logs in to the respective environment
    3. Then it clears all previous execution environment state data
    4. Then it realigns the required `data*.tf` states
    5. Then it runs the `run_prebuild.sh` scripts if needed to compile lambda source code
    6. Then it initialises the terraform module and ignores any states generate related to ECR and KMS
    7. Finally it executes the actual terraform command

## Login

We use `uat` as the jumphost
```
uat (empty role) --> uat (admin)
uat (empty role) --> sit (admin)
uat (empty role) --> prd (admin)
```
(WIP: to add a diagram for illustration)

~/.aws/config for SSO
```
[profile aib-sso]
sso_start_url = https://gccsso.awsapps.com/start#/
sso_region = ap-southeast-1
sso_account_id = <uat account id>
sso_role_name = agency_assume_local
output = json
```

login.<env>.sh
```
#!/bin/bash

echo "assume role"
export AWS_PROFILE=<IAM role profile name>
```

## Execution

Enter the respective directory and execute 
```
# e.g. 
# cd 0101-sharedsvc-s3
../run.sh <action> <environment>
```

Run the script below to execute deploy the entire infrastructure

```shell
./all.sh apply ? sit -auto-approve > all.sit.20240905.txt
```

Breaking it down:
- ./all.sh apply << what action? apply, destroy, blah.
- ? << prefix of folders, ? for ALL, 0 for 0*, 01 for 01*
- sit << the env
- --auto-approve << this is auto approve the deployment without you to type yes when it detects changes
- > all.sit.20240905.list << pipe all the output into this files so that when shit happens you can trace back (edited) 
