
echo 'This is not working because the AOSS can only be deleted from within VPC.'

# Generate a JSON payload with sequenced index
for i in {0..3}; do
  curl -X DELETE https://1kb39ee6il7h39bhmi3c.ap-southeast-1.aoss.amazonaws.com/$i
done