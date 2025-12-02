ARG ATLAS_BASE_IMAGE=python
ARG ATLAS_BASE_IMAGE_TAG=3.11.4-slim-bookworm

FROM $ATLAS_BASE_IMAGE:$ATLAS_BASE_IMAGE_TAG AS build

ARG ATLAS_USER
ARG ATLAS_TOKEN
ARG VERSION
ARG RELEASE_DATE
ARG GIT_BRANCH
ARG GIT_COMMIT_HASH
ARG KEY_PASS="c50e0949-b5a5-4efb-8918-3d41ff0ef27e"

# Install Python dependencies
COPY agents-api/pyproject.toml agents-api/poetry.lock README.md agents-api/
COPY aibots aibots
WORKDIR agents-api
RUN poetry config http-basic.atlas $ATLAS_USER $ATLAS_TOKEN && \
    poetry install --without dev --no-root && \
    echo $(printf '{"version": "%s", "release_date": "%s", "commit": "%s", "branch": "%s"}' "$VERSION" "$RELEASE_DATE" "$GIT_COMMIT_HASH" "$GIT_BRANCH") > version.json

# Create self-signed CA Certificate and add to root store
RUN openssl genpkey -out localhost.pem -outform PEM -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -pass pass:$KEY_PASS && \
    openssl req -new -key localhost.pem -out localhost.csr \
        -subj "/C=SG/ST=Pasir Panjang/L=MBC/O=GovTech/OU=aibots/CN=aibots.gov.sg/emailAddress=david_tw_lee@tech.gov.sg" && \
    openssl x509 -signkey localhost.pem -in localhost.csr -req -days 1825 -out localhost.crt && \
    cp localhost.crt /usr/local/share/ca-certificates/localhost.crt && \
    update-ca-certificates

FROM build AS production

# Install the source code as a Python package
COPY agents-api/agents agents
RUN poetry install --only-root --compile

# Allow access to reserved ports (80, 443) and set permissions
RUN setcap 'cap_net_bind_service=+ep' $HOME/agents-api/agents/__main__.py && \
    chmod 777 $HOME/agents-api/agents/__main__.py

# Run the component
CMD ["python3", "-m", "agents"]
