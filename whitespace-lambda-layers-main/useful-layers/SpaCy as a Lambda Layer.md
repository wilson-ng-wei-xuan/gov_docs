# Create SpaCy Lambda Layer

To use SpaCy in AWS Lambda function, you can create a lambda layer to include SpaCy library and necessary packages.  

Apart from SpaCy library, it is common to download other supporting packages. 



### Create Zip File for Lambda Layer

Update following script if necessary:

* Python version
* File name of requirements.txt
* Add other NLTK packages to download



**The NLTK packages are downloaded and put in `/python/nltk_data` folder. We will need to set the `NLTK_DATA` folder in the Lambda function.****

```
# Create virtual environment
virtualenv --python=python3.8 v-env

source ./v-env/bin/activate

# Install library and download package
pip install -r spacy_requirements.txt
python -c "python -m spacy download en_core_web_sm"

# Copy library and package(s) into /python folder
mkdir python
cp -R v-env/lib/python3.8/site-packages/* ./python

# Create zip file
zip -r spacy.zip python --exclude python/*.zip* --exclude python/__pycache__

# Clean up
rm -rf v-env
rm -rf python
```



### Publish Lambda Layer using AWS CLI



```
aws lambda publish-layer-version --layer-name nltk --zip-file fileb://./nltk.zip --compatible-runtimes python3.8
```



## Usage

In the lambda function, include following line to set the NLTK_DATA path. 

```python
nltk.data.path.append("/opt/python/nltk_data")
```

