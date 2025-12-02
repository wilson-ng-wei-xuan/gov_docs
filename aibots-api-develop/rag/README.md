### Running Unit Tests
Running unit tests for parsers
```
nox -s unittests
```

### Setting up dev environment for testing Lambdas locally

Adapted from [AWS non-base Python](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-clients)

1. Install the Lambda Emulator

```shell
mkdir -p ~/.aws-lambda-rie && \
    curl -Lo ~/.aws-lambda-rie/aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie && \
    chmod +x ~/.aws-lambda-rie/aws-lambda-rie
```

2. Run the emulator

```shell
docker run --platform linux/amd64 -d -v ~/.aws-lambda-rie:/aws-lambda -p 9000:8080 \
    --entrypoint /aws-lambda/aws-lambda-rie \
    <image>:<tag> \
    /usr/local/bin/python -m awslambdaric <lambda_function>
```