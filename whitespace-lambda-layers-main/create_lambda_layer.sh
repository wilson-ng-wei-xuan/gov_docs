#!/bin/bash

##################
# Create zip file to deploy an AWS Lambda Layer

# Need to install virtualenv and aws-cli
#   sudo apt install python3-virtualenv

if [ $# != 1 ] && [ $# != 2 ]; then
    echo "Usage: ./create_lambda_layer.sh <SOURCE_FOLDER> [<PYTHON_VERSION>]"
    echo "Example: ./create_lambda_layer.sh pandas_layer"
    echo "Example: ./create_lambda_layer.sh pandas_layer python3.8"
    echo "Usage: ./create_lambda_layer.sh <REQUIREMENTS_FILE> [<PYTHON_VERSION>]"
    echo "Example: ./create_lambda_layer.sh pandas_layer/requirements.txt"
    echo "Example: ./create_lambda_layer.sh pandas_layer/requirements.txt python3.8"
    exit 1
fi

if [ $# == 2 ]; then
    PYTHON_VERSION=$2
else
    PYTHON_VERSION="python3.8"
fi

if [ -d "$1" ]; then
    echo "$1 is a folder"
    FILEBASENAME=$1
    SOURCE_FOLDER=$1
    ZIP_FILE="$1.zip"
    REQUIREMENTS_FILE="$1/requirements.txt"
elif [ -f "$1" ]; then
    echo "$1 is a file"
    SOURCE_FOLDER=""
    FILEBASENAME="${1%.*}"
    ZIP_FILE="${1%.*}.zip"
    REQUIREMENTS_FILE=$1
else
    echo "First argument must be either a folder or a requirement file"
    exit 1
fi

echo "Create layer $FILEBASENAME ($PYTHON_VERSION) from $SOURCE_FOLDER/$REQUIREMENTS_FILE to $ZIP_FILE" 

# Remove existing zip file
echo "Removing existing $ZIP_FILE ./python ./v-env"
rm -rf $ZIP_FILE python v-env

# Create virtual env and install libraries
echo "Create virtual environment for $PYTHON_VERSION"
virtualenv --python=$PYTHON_VERSION v-env
source ./v-env/bin/activate

echo "Install library files from $REQUIREMENTS_FILE"
pip install -r $REQUIREMENTS_FILE 
deactivate

# Extract and zip installed libraries
# The folder name MUST be python and python.zip
echo "Create zip file $ZIP_FILE from libraries"
mkdir python
cd python
cp -r ../v-env/lib/$PYTHON_VERSION/site-packages/* .
# Copy requirements file into zip folder too as a record
cp ../$REQUIREMENTS_FILE .

# Copy whole SOURCE_FOLDER into python folder too
if [ $SOURCE_FOLDER != "" ]; then
    cp -r ../$SOURCE_FOLDER .
fi

# Delete unused folders before zipping
find . -type d -name "tests" -exec rm -rfv {} +
find . -type d -name "__pycache__" -exec rm -rfv {} +

# # Zip folder
cd ..
zip -r $ZIP_FILE python \
    --exclude python/*.zip* \
    --exclude python/__pycache__ 

# # Clean up
echo "Clean up..." 
rm -rf python
rm -rf v-env

# # Publish it to AWS
#echo "Create lambda layer..."
#aws lambda publish-layer-version --layer-name $FILEBASENAME --zip-file fileb://$ZIP_FILE --compatible-runtimes $PYTHON_VERSION
