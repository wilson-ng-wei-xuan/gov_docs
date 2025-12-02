# Create NLTK Lambda Layer

To use NTLK in AWS Lambda function, you can create a lambda layer to include NTLK library and necessary packages.  

But apart from NTLK library, it is common to download other NLTK supporting packages. 



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
pip install -r nltk_requirements.txt
python -c "import nltk; nltk.download('stopwords', download_dir='./nltk_data')"
python -c "import nltk; nltk.download('punkt', download_dir='./nltk_data')"

# Copy library and package(s) into /python folder
mkdir python
cp -R v-env/lib/python3.8/site-packages/* ./python
cp -R nltk_data ./python

# Create zip file
zip -r nltk.zip python --exclude python/*.zip* --exclude python/__pycache__

# Clean up
rm -rf nltk_data
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

