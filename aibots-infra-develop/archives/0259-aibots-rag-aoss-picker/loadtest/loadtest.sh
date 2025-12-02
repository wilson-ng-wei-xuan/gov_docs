# Generate a JSON payload with sequenced index

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <start> <end>"
    exit 1
fi

# converts to number
start=$1
end=$2

# Check if start is smaller than end
if [ "$start" -ge "$end" ]; then
    echo "Error: Start value must be smaller than end value."
    exit 1
fi

for ((i = start; i <= end; i++)); do
  echo $i
  # Generate a JSON payload with sequential numbers
  # payload='{"flow": "'$(date +%s)'", "key2": "'$(shuf -i 1-100 -n 1)'"}'
  payload='{"flow": "upsert", "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/story.txt", "index_name": "'$i'"}'

  # Save the payload to a temporary file
  echo $payload > payload.json

  # Invoke the Lambda function with the JSON payload
  aws lambda invoke --function-name lambda-sitezapp-aibots-rag-aio-img --payload fileb://payload.json output.txt

  # display the output
  cat output.txt
done