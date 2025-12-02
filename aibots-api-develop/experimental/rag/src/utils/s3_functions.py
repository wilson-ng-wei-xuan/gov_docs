import boto3

s3 = boto3.client('s3')

# Function to upload file to S3
def upload_to_s3(file, upload_location):
    bucket_name = '/'.join(upload_location.split("/")[:3]).replace("s3://", "")
    folder_name = '/'.join(upload_location.split("/")[3:])
    folder_name = folder_name + ("/" if folder_name[-1] !="/" else folder_name)
    # Upload the file
    s3.upload_fileobj(file, bucket_name, folder_name+file.name)
    
def list_files_bucket(upload_location):
    bucket_name = '/'.join(upload_location.split("/")[:3]).replace("s3://", "")
    folder_name = '/'.join(upload_location.split("/")[3:])
    folder_name = folder_name + ("/" if folder_name[-1] !="/" else folder_name)
    # List the objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name )

    # Check if objects are present in the bucket
    if 'Contents' in response:
        return [obj['Key'] for obj in response['Contents']]
    else:
        print("No files found in the bucket.")