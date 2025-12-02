import json
import boto3
import os

from io import BytesIO

import util_tool # utility for generic tools
import util_http # utility for http related

import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import logging
logging.getLogger().setLevel(logging.INFO)

import re
email_validation = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

s3_client = boto3.client('s3')
s3_sendemail_bucket = os.environ['SHAREDSVC_EMAIL__BUCKET']

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))

  dts_now = util_tool.local_datetimestamp()
  payload = util_http.payload_extraction( event )

  smtp_key = payload.get('smtp_key','')
  name_from = payload.get('sender_name','')
  email_from = payload.get('sender','').replace(' ','')
  reply_to = payload.get( 'reply_to', [] )
  email_to = payload.get( 'to', [] )
  email_cc = payload.get( 'cc', [] )
  email_bcc = payload.get( 'bcc', [] )
  email_subject = payload.get('subject','')
  text = payload.get('text','')
  email_content = payload.get('html','')
  encoding = payload.get('encoding','UTF-8')
  email_attachment = payload.get('email_attachment','')

################################################################################
# validate payload                                                             #
################################################################################
  # You must have the email_from, so it is not checking if empty
  if not ValidateEmail(email_from):
    logging.info('invalid email_from >> {}'.format( email_from ) )
    return {
      'statusCode': 400,
      'headers': { 'Content-Type': 'application/json' },
      'body': json.dumps({ 'from ': context.function_name, 'msg': 'invalid email_from >> {}'.format( email_from ) })
    }

  # You must have the email_to, so it is not checking if empty
  if not all( [ValidateEmail( email.strip() ) for email in email_to ] ):
    logging.info('invalid email_to >> {}'.format( email_to ) )
    return {
      'statusCode': 400,
      'headers': { 'Content-Type': 'application/json' },
      'body': json.dumps({ 'from ': context.function_name, 'msg': 'invalid email_to >> {}'.format( email_to ) })
    }
  
  # email_cc can be empty
  if email_cc != '' and not all( [ValidateEmail( email.strip() ) for email in email_cc ] ):
    logging.info( 'invalid email_cc address >> {}, continue.'.format( email_cc ) )

  # email_bcc can be empty
  if email_bcc != '' and not all( [ValidateEmail( email.strip() ) for email in email_bcc ] ):
    logging.info( 'invalid email_bcc address >> {}, continue.'.format( email_bcc ) )

  response = SendEmail( smtp_key, name_from, email_from, email_to, email_cc, email_bcc, email_subject, email_content, email_attachment )

  s3_client.put_object(
    Bucket = s3_sendemail_bucket,
    Key = 'status/{}/{}/{}/{}_{}.log.gz'.format( dts_now['year'], dts_now['month'], dts_now['day'], dts_now['dts'], util_tool.random_generator() ),
    Body = util_tool.gzip_data( '"{}","{}","{}","{}","{}","{}","{}","{}","{}"'.format( dts_now['dts'], response['statusCode'], json.loads(response['body'])['msg'], name_from, email_from, email_to, email_cc, email_bcc, email_subject ) )
  )

  if email_attachment:
    clean_up( s3_sendemail_bucket, [ email_attachment ] )

  logging.info('event ended.')
  return response


################################################################################
# clean_up                                                                     #
################################################################################
def clean_up( src_bucket, src_file_list ):
  logging.info('clean_up activated.' )

  try:
    for src_file in src_file_list:
      logging.info( "deleting s3://{}/{}".format(src_bucket, src_file) )
      s3_client.delete_object( Bucket=src_bucket, Key=src_file )

  except Exception as e:
    logging.error( '{} >> error clean_up >> {}'.format( '', str(e) ) ) # sends to the channel
    logging.info('exception ended.')


################################################################################
# validating an Email                                                          #
################################################################################
def ValidateEmail( email ):
    # pass the regular expression
    # and the string into the fullmatch() method
    if( re.fullmatch( email_validation, email ) ):
        return True
 
    else:
        return False

################################################################################
# Send HTML email                                                              #
################################################################################

def SendEmail( smtp_key, name_from, email_from, email_to, email_cc, email_bcc, email_subject, email_content, email_attachment ):
  logging.info( 'SendEmail activated.' )

  HOST = 'email-smtp.ap-southeast-1.amazonaws.com'
  PORT = 587

  # Replace smtp_username with your Amazon SES SMTP user name.
  SMTP_USER = smtp_key.get('SMTP_USER', '')
  # Replace smtp_password with your Amazon SES SMTP password.
  SMTP_PASSWORD = smtp_key.get('SMTP_PASSWORD', '')

  # Create message container - the correct MIME type is multipart/alternative.
  msg = MIMEMultipart()
  msg['From'] = email.utils.formataddr((name_from, email_from))
  # email_to  = list( email_to.split(',') )
  # email_cc  = list( email_cc.split(',') )
  # email_bcc  = list( email_bcc.split(',') )
  msg['To'] = ', '.join(email_to) # for some reason, it MUST join convert the LIST back into the STRING then it will work.
  msg['Cc'] = ', '.join(email_cc)
  msg['Bcc'] = ', '.join(email_bcc)
  msg['Subject'] = email_subject
  
  # Attach parts into message container.
  # According to RFC 2046, the last part of a multipart message, in this case
  # the HTML message, is best and preferred.
  msg.attach( MIMEText(email_content, 'html') )

  if len(email_attachment) > 0:
    try:
      buf = BytesIO()
      s3_client.download_fileobj(Bucket=s3_sendemail_bucket, Key=email_attachment, Fileobj=buf)
      buf.seek(0)
      binary_data = buf.read()
  
      part = MIMEBase("application", "octet-stream")
      part.set_payload( binary_data )
      encoders.encode_base64(part)
      # the "" is needed for attaching files with space in name
      part.add_header( 'Content-Disposition', 'attachment', filename='"%s"' %email_attachment.split('/')[-1] )
      msg.attach(part)
    except Exception as e:
      logging.error('Error: {}'.format( e ) )
      return {
        'statusCode': 400,
        'headers': { 'Content-Type': 'application/json' },
        'body': json.dumps({ 'msg': str(e) })
      }

  # Try to send the message.
  try:
    server = smtplib.SMTP(HOST, PORT)
    server.ehlo()
    server.starttls()
    #stmplib docs recommend calling ehlo() before & after starttls()
    server.ehlo()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message( msg )
    server.close()
  # Display an error message if something goes wrong.
  except Exception as e:
    logging.error('Error: {}'.format( e ) )
    return {
      'statusCode': 400,
      'headers': { 'Content-Type': 'application/json' },
      'body': json.dumps({ 'msg': str(e) })
    }
  else:
    logging.info('Email sent.')
    return {
      'statusCode': 200,
      'headers': { 'Content-Type': 'application/json' },
      'body': json.dumps({ 'msg': 'Email sent.' })
    }