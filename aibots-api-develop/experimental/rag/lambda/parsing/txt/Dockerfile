# Use the official Python image from the Docker Hub
FROM public.ecr.aws/lambda/python:3.9

# Set the working directory in the container
WORKDIR /var/task

# Copy the current directory contents into the container at /app
COPY . /var/task

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Run the script
CMD ["lambda_function.lambda_handler"]