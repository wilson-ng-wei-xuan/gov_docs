# Use the official Python image from the Docker Hub
FROM public.ecr.aws/lambda/python:3.9

# Set the working directory in the container
WORKDIR /var/task

# Copy the current directory contents into the container at /app
COPY . /var/task

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create the /tmp directory and make it writable
RUN mkdir -p /tmp && chmod 777 /tmp

# Download NLTK data to the /tmp directory
RUN python -m nltk.downloader -d /tmp punkt averaged_perceptron_tagger

# Set environment variable for NLTK data
ENV NLTK_DATA=/tmp

# Run the script
CMD ["lambda_function.lambda_handler"]