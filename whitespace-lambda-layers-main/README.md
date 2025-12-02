# Script to Create AWS Lambda Layer

This script creates a zip file with python libraries, which can be used to deploy as an AWS Lambda Layer. Optionally, you can use AWS CLI to deploy the layer to AWS.

It creates a `python` folder with libraries files indicated in requirements.txt in SOURCE_FOLDER. It also copies SOURCE_FOLDER into `python` folder too.



The `useful-layers` contains a few common lambda layers.



#### Usage 1

Create with a source folder. All files in the source folder will be included in the zip file. Zip file will have the same name as the folder, i.e. `source_folder.zip`.

    ./create_lambda_layer.sh <SOURCE_FOLDER> [<PYTHON_VERSION>]

Examples:

    ./create_lambda_layer.sh iso3166

```
./create_lambda_layer.sh iso3166 python3.8
```



#### Usage 2:

Create with a requirements.txt file.

```
./create_lambda_layer.sh <REQUIREMENTS_FILE> [<PYTHON_VERSION>]
```

Examples:

```
./create_lambda_layer.sh iso3166/requirements.txt
```

```
./create_lambda_layer.sh iso3166/requirements.txt python3.8
```



### Publish to AWS

#### Option 1

- Use AWS Management Console to create AWS Lambda layer manually using the zip file

#### Option 2

- Set the default profile of the AWS CLI using `export AWS_DEFAULT_PROFILE=<PROFILE>`.
- Uncomment last line in `create_lambda_layer.sh` file.
