FROM public.ecr.aws/lambda/python:3.12

# Copy function code
COPY ./source/image/app.py ${LAMBDA_TASK_ROOT} 
# COPY ./source/image/requirements.txt  ${LAMBDA_TASK_ROOT} 

# # install dependencies
# RUN pip3 install --user -r requirements.txt

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.lambda_handler" ]