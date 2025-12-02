FROM python:3.10-slim

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
CMD streamlit run --server.port 8501 AIBots_Evaluator.py