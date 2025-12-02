FROM python:3.10-slim

RUN apt-get update && apt-get install ffmpeg -y

WORKDIR /app

## For pip
COPY requirements.txt .

#RUN cat requirements.txt | xargs -n 1 pip install --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir


# Copy local code to the container image.
COPY . .

# Run the web service on container startup.
EXPOSE 8501
CMD streamlit run --server.port 8501 streamlit_app.py