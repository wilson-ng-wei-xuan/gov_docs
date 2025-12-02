# AI Bots API

# CLI commands

# Running AIBots backend locally

1. Download pyenv, virtualenv, poetry, nox,

2. Download atlas using poetry

```shell
poetry config virtualenvs.create false --local  
poetry config http-basic.atlas registry 6YPcXxNma8jnqLsucACd
poetry update   
```

3.	Create and activate virtual environment e.g. if using python 3.11.9

```shell
pyenv virtualenv 3.11.9 aibots3.11.9       
pyenv activate aibots3.11.9
```

4.	Generate ssl key in the AIBOTS-API/aibots

```shell
brew install openssl
```

```shell
openssl req -new -newkey rsa:4096 -nodes -keyout localhost.key -out localhost.csr -subj "/CN=localhost"

openssl x509 -req -days 365 -in localhost.csr -signkey localhost.key -out localhost.crt

cat localhost.key localhost.crt > localhost.pem
```

5.	add environment variables into .env file or launch.json for vscode (some environment variables can be found in compose.test.yaml)

6. add cloudflare_CA.pem in AIBOTS_API by following the steps found in the link below

[`cloudflare certificate for python on mac`] (https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/user-side-certificates/install-cloudflare-cert/#python-on-mac-and-linux)

7. pull atlas docker image 

```shell
docker login -u registry -p {ATLAS_TOKEN} registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/
docker pull registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/atlas-mongo/auth:latest
```

8. pull moonshot docker image
```shell
docker login -u registry -p {MOONSHOT_TOKEN} registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/
docker pull registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/nous/nous-api:sit 
```

9. start the virtual env
```shell
nox -s start_dev_env   
```

## Building Locally

```shell
export GIT_COMMIT_HASH=`git rev-parse HEAD` GIT_BRANCH=`git rev-parse --abbrev-ref HEAD` RELEASE_DATE=$(date +"%Y-%m-%dT%H:%M:%S%:z") VERSION=1.0.0
docker compose -f compose.build.yaml build
```

## Running Locally

```shell
docker compose up -d
curl -k https://127.0.0.1/internals/configs  # Ignore insecure self-signed certificate
```

# Supported Environment Variables

| Name                   | Description                                                                                                         | Required? | Default Value  | Remarks                                                    |
|------------------------|---------------------------------------------------------------------------------------------------------------------|-----------|----------------|------------------------------------------------------------|
| AWS_ID                 | AWS Account ID, accepts a 10 digit string.                                                                          | Y         | -              | -                                                          |
| DB_USER                | Database host User, accepts a valid url escaped string                                                              | Y         | -              | -                                                          |
| DB_PASSWORD            | Database host Password, accepts a valid url escaped string                                                          | Y         | -              | -                                                          |
| DB_URL                 | Database host URL, accepts a valid FQDN string                                                                      | Y         | -              | -                                                          |
| COMPONENT              | Component name, in the event that clustering is required, accepts a string value                                    | N         | aibots         | -                                                          |
| LOGGING_LEVEL          | Logging level verbosity, accepts an integer value from the following set (10, 20, 30, 40, 50)                       | N         | 20             | Set to 10 for local development testing                    |
| DEBUG                  | Indicates if Debug mode should be initialised, logs will be written to file. Accepts a boolean integer value (0, 1) | N         | 0              | Set to 1 for local development testing                     |
| AWS_REGION             | AWS Region to be used, accepts a string value                                                                       | N         | ap-southeast-1 | -                                                          |
| AWS_BUCKETS__ANALYTICS | AWS Bucket to be used for Analytics, accepts a string value                                                         | N         | analytics/     | -                                                          |
| AWS_ENDPOINT_URL       | AWS endpoint url to connect to AWS Services, accepts a valid FQDN                                                   | N         | None           | Mainly for                                                 |
| HOST                   | Host to listen to, accepts a host string                                                                            | N         | 127.0.0.1      | Set to 0.0.0.0 in production environments                  |
| PORT                   | PORT to listen on, accepts an integer value                                                                         | N         | 443            | Defaults to 443 for SSL                                    |
| USE_SSL                | Indicates if SSL should be used, accepts a boolean integer value (0, 1)                                             | N         | 1              | Set to 0 for local development testing                     |
| SSL_KEYFILE            | SSL key file to support TLS functionality, accepts a path value                                                     | N         | localhost.pem  | Not required to set, defaults to self-signed cert in image |
| SSL_CERTFILE           | SSL certificate file to support TLS functionality, accepts a path value                                             | N         | localhost.crt  | Not required to set, defaults to self-signed cert in image |
| TOKEN_EXPIRY           | Timedelta (in hours) after which the JWT token will expire, accepts an integer value greater than 0                 | N         | localhost.pem  | Not required to set, defaults to self-signed cert in image |

---
**NOTE**

The double underscore in AWS_BUCKETS__ANALYTICS is required to import this as a nested structure i.e.

{
    "aws_bucket": {
        "analytics": ENV_VAR
    }
} 

---

### 

# Todos
~~1. Add linter~~
~~2. Integrate proper JSON logger~~
3. Extract common reusable elements to launchpad framework
4. Migrate error handling to Middleware