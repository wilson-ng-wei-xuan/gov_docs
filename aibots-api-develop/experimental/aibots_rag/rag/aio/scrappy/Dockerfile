ARG ATLAS_BASE_IMAGE=python
ARG ATLAS_BASE_IMAGE_TAG=3.11.8-slim-bookworm

FROM $ATLAS_BASE_IMAGE:$ATLAS_BASE_IMAGE_TAG AS build

COPY requirements.txt .


# Install build dependencies
RUN apt-get update && \
  apt-get install -y build-essential libssl-dev libffi-dev python3-dev \
  ffmpeg libsm6 libxext6 poppler-utils libleptonica-dev tesseract-ocr \
  libtesseract-dev python3-pil tesseract-ocr-eng tesseract-ocr-script-latn && \
  # Install dependencies
  pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
  pip install --no-cache-dir -r requirements.txt && rm requirements.txt && \
  pip install --no-cache-dir --target . awslambdaric && \
  # Download NLTK data
  mkdir -p nltk && \
  chmod 777 nltk && \
  python -m nltk.downloader -d tmp punkt averaged_perceptron_tagger && \
  # Cleanup build dependencies
  apt-get remove -y curl build-essential libssl-dev libffi-dev python3-dev && \
  apt-get autoremove -y && apt-get autoclean -y

# STAGE: main
# -----------
# Image used for main.
FROM build AS main

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV NUMBA_CACHE_DIR=/tmp

# Set environment variable for NLTK data
ENV NLTK_DATA=/nltk

COPY . .

# Run the component
ENTRYPOINT ["/usr/local/bin/python", "-m", "awslambdaric"]
CMD ["lambda_function.lambda_handler"]