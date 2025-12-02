FROM python:3.10-slim


RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install poppler-utils -y
RUN apt-get install libleptonica-dev tesseract-ocr libtesseract-dev python3-pil tesseract-ocr-eng tesseract-ocr-script-latn -y

WORKDIR /app

## For pip
COPY requirements.txt .

#RUN cat requirements.txt | xargs -n 1 pip install --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir


# Copy local code to the container image.
COPY . .

# Copy model from S3
#RUN aws s3 cp s3://mdeberta-class/model model

# Run the web service on container startup.
EXPOSE 8501
CMD streamlit run --server.port 8501 home.py