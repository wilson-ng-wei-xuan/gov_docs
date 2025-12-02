import json
import logging
logging.getLogger().setLevel(logging.INFO)

import base64

from urllib.parse import parse_qs

# pass in the event
# return body
def payload_extraction( event ):
  logging.info('payload_extraction activated')

  body = base64.b64decode(event['body']) if len(event['body']) > 0 else b""
  body = json.loads( body.decode("utf-8") )

  logging.debug("Payload >> {}".format(body))
  
  return body

# pass in the event
# return body
def html_payload_extraction( event ):
  body = base64.b64decode(event['body']) if len(event['body']) > 0 else b""
  body = parse_qs( body.decode("utf-8") )

  for k,v in body.items():
    # strip away whitespaces in key value pair, including comma separated value
    # body[k] = ','.join([x.strip() for x in v[0].split(',')])
    # strip away whitespaces in key value pair, keeping only the first 20 characters (to prevent SQL injection), including comma separated value
    body[k] = ','.join([x.strip()[:20] for x in v[0].split(',')])

  logging.debug("Payload >> {}".format(body))
  
  return body