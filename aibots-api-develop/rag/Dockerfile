ARG ATLAS_BASE_IMAGE=python
ARG ATLAS_BASE_IMAGE_TAG=3.11.4-slim-bookworm

FROM $ATLAS_BASE_IMAGE:$ATLAS_BASE_IMAGE_TAG AS build

ARG RAG_COMPONENT_PATH
ARG ATLAS_USER
ARG ATLAS_TOKEN
ARG VERSION
ARG RELEASE_DATE
ARG GIT_BRANCH
ARG GIT_COMMIT_HASH
ARG KEY_PASS="c50e0949-b5a5-4efb-8918-3d41ff0ef27e"

# Install Python dependencies
COPY $RAG_COMPONENT_PATH/pyproject.toml $RAG_COMPONENT_PATH/poetry.lock $RAG_COMPONENT_PATH/
COPY aibots aibots
WORKDIR $RAG_COMPONENT_PATH
RUN poetry config http-basic.atlas $ATLAS_USER $ATLAS_TOKEN && \
    poetry install --without dev --no-root && \
    pip3 install --target . awslambdaric && \
    echo $(printf '{"version": "%s", "release_date": "%s", "commit": "%s", "branch": "%s"}' "$VERSION" "$RELEASE_DATE" "$GIT_COMMIT_HASH" "$GIT_BRANCH") > version.json

FROM build AS production

ARG RAG_COMPONENT_PATH

# Install the source code as a Python package
COPY $RAG_COMPONENT_PATH/* ./

# Run the component
ENTRYPOINT ["/usr/local/bin/python", "-m", "awslambdaric"]
CMD ["lambda_function.lambda_handler"]

FROM production AS nltk_production

ENV NUMBA_CACHE_DIR=/tmp

ARG RAG_COMPONENT_PATH

# Download NLTK data
RUN mkdir -p nltk && \
    chmod 777 nltk && \
    python -m nltk.downloader -d tmp punkt averaged_perceptron_tagger

# Set environment variable for NLTK data
ENV NLTK_DATA=$RAG_COMPONENT_PATH/nltk

FROM nltk_production AS pdf_production

ARG RAG_COMPONENT_PATH
