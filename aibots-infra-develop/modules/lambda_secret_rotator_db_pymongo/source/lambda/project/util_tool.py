import json
import logging
logging.getLogger().setLevel(logging.INFO)

from datetime import datetime, timedelta

import base64
from io import BytesIO
import gzip

import string
import random

################################################################################
# return current datetime as string
def local_datetimestamp():
  GMT = 8
  now = datetime.now() + timedelta( hours = GMT )
 
  logging.info( 'local_datetimestamp >> {}'.format( now ) )

  return {
    "year": now.strftime("%Y"),
    "month": now.strftime("%m"),
    "day": now.strftime("%d"),
    "hour": now.strftime("%H"),
    "minute": now.strftime("%M"),
    "second": now.strftime("%S"),
    "dts": now.strftime("%Y-%m-%dT%H:%M:%S+0{}:00".format(GMT))
  }

################################################################################
# compress the data
def gzip_data( data ):
  compressed = BytesIO()
  with gzip.GzipFile(fileobj=compressed, mode='w') as f:
    f.write(data.encode('utf-8'))

  return compressed.getvalue()

################################################################################
# compress the data before returning
# data shall be UTF8 decoded, e.g. non binary payload.
# # content = content.decode('UTF8')
# # headers["Content-Encoding"] = "gzip" # you need to set gzip Content-Encoding
# # isBase64Encoded = True # Base64 to True
# # content = util.gzip_b64encode(content)
################################################################################
def gzip_b64encode( data ):
#   compressed = BytesIO()
#   with gzip.GzipFile(fileobj=compressed, mode='w') as f:
#     # # This is working
#     # json_response = json.dumps(data)
#     # f.write(json_response.encode('utf-8'))

#     f.write(data.encode('utf-8'))

#   return base64.b64encode( compressed.getvalue() ).decode('ascii')
  return base64.b64encode( gzip_data( data ) ).decode('ascii')

################################################################################

def random_generator( size = 8, chars = string.ascii_lowercase + string.digits ):

  return ''.join( random.choice( chars ) for _ in range( size ) )