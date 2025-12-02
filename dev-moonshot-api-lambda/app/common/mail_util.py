import json
import os
import pathlib
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import markdown

import boto3

from app.config import LOCAL_FOLDER, logger
from app.common.mail_task_type import MailTaskType
from app.utils.file_util import hash_by_md5
from app.utils.re_util import (find_placeholders_in_text,
                               replace_image_urls_with_cid_in_html)
from app.utils.s3_util import (download_file_object_from_bucket,
                               key_exists_in_bucket, list_files_in_bucket,
                               read_file_from_bucket)
from app.utils.ses_util import send_raw_email
from app.utils.url_util import download_file_from_url

session = boto3.session.Session()
s3_client = session.client('s3')
ses_client = session.client('ses')
sqs_client = session.client('sqs')

ADMIN_EMAIL = os.environ.get('EMAIL_ADMIN', 'data@tech.gov.sg')

def construct_email_from_content_and_embed_images(subject: str, from_email: str, to_emails: List[str],
                                                  message_html: str = '', message_text: str = '',
                                                  reply_to_email: Optional[str] = None,
                                                  cc_emails: Optional[List[str]] = None) -> MIMEMultipart:
    """
    Create an instance of MIMEMultipart from HTML file by embedded images from URLs in HTML.
    """
    image_urls, message_html = replace_image_urls_with_cid_in_html(
        message_html)

    msg = construct_email_from_content(subject, from_email, to_emails, message_html, message_text, reply_to_email,
                                       cc_emails)
    return msg


def construct_email_from_content(subject: str, from_email: str, to_emails: List[str],
                                 message_html: str = '', message_text: str = '',
                                 reply_to_email: Optional[str] = None,
                                 cc_emails: Optional[List[str]] = None) -> MIMEMultipart:
    """
    Create an instance of MIMEMultipart related-subtype email with html and text content
    :param subject: Email subject
    :param from_email: Email sender
    :param to_emails: List of email addresses
    :param message_html: HTML message
    :param message_text: TEXT message
    :param reply_to_email: Optional reply-to email address
    :param cc_emails: Optional list of cc email addresses
    :return: Email message
    """

    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ','.join(to_emails)
    if reply_to_email:
        msg['Reply-to'] = reply_to_email
    if cc_emails:
        msg['Cc'] = ", ".join(cc_emails)
    # Set the multipart email preamble attribute value
    msg.preamble = '====================================================='
    # Create a 'alternative' MIMEMultipart object. We will use this object to save plain text format content.
    msg_alternative = MIMEMultipart('alternative')
    # Attach a MIMEText object with plain text content
    msg_alternative.attach(MIMEText(message_text))
    # Attach a MIMEText object with html content with images
    msg_alternative.attach(MIMEText(message_html, 'html'))
    # Attach the above object to the root email message.
    msg.attach(msg_alternative)

    return msg


def attach_local_images_to_email(msg: MIMEMultipart, images_folder: str) -> MIMEMultipart:
    """
    Add all images in a local folder into email message
    """
    path_images_folder = Path(images_folder)
    if path_images_folder.exists():
        for image_file in path_images_folder.iterdir():
            if image_file.is_file():
                with open(str(image_file), 'rb') as fp:
                    img_data = MIMEImage(
                        fp.read(), _subtype=image_file.suffix[1:] if image_file.suffix else '')
                    img_data.add_header('Content-ID', f'<{image_file.stem}>')
                msg.attach(img_data)
    else:
        raise Exception(f'Image folder not found: {images_folder}')
    return msg


def attach_s3_images_to_email(msg: MIMEMultipart, s3_client, bucket_name: str,
                              s3_file_keys: List[str]) -> MIMEMultipart:
    """
    Add all images, which match key prefix in a s3 bucket, to an email message
    """
    for file_key in s3_file_keys:
        if key_exists_in_bucket(s3_client, bucket_name, file_key):
            obj = download_file_object_from_bucket(
                s3_client, bucket_name, file_key)
            img_data = MIMEImage(obj['Body'].read())
            img_data.add_header('Content-ID', f'<{file_key}>')
            msg.attach(img_data)
    return msg


def attach_s3_files_to_email(msg: MIMEMultipart, s3_client, bucket_name: str,
                             s3_file_keys: List[str]) -> MIMEMultipart:
    """
    Attach all files, which match key prefix in a S3 bucket, to an email message
    """
    for file_key in s3_file_keys:
        if key_exists_in_bucket(s3_client, bucket_name, file_key):
            p = Path(file_key)
            file_name = p.name
            obj = download_file_object_from_bucket(
                s3_client, bucket_name, file_key)
            part = MIMEApplication(
                obj['Body'].read(), _subtype=p.suffix[1:] if p.suffix else '')
            part.add_header("Content-Disposition",
                            'attachment', filename=file_name)
            msg.attach(part)
        else:
            logger.warning(
                f"Failed to attach s3 files to email: Missing file {file_key}")
    return msg


def attach_local_files_to_email(msg: MIMEMultipart, file_paths: List[str]) -> MIMEMultipart:
    """
    Attach all files in local folder to email message
    """
    for file_path in file_paths:
        p = Path(file_path)
        if p.exists():
            with open(file_path, 'rb') as f:
                part = MIMEApplication(
                    f.read(), _subtype=p.suffix[1:] if p.suffix else '')
                part.add_header("Content-Disposition",
                                'attachment', filename=p.name)
                msg.attach(part)
        else:
            logger.warning(
                f"Failed to attach_local_files_to_email: Missing file: {file_path}")
    return msg


def replace_all_substrings(text: str, dic: Dict[str, str]) -> str:
    """
    Replace all placeholders in the text
    Args:
        text: original text
        dic: Dictionary with key=old-substring value=new-substring
    Return:
        Updated text
    """
    for old_str, new_str in dic.items():
        text = text.replace(old_str, new_str)
    return text


def prepare_html_message_to_embed_images(html: str) -> Tuple[str, str]:
    """
    Extract any image URL from HTML and replace them with their respective cid.
    Download image from URL into a folder.
    Args:
        html: Original HTML
    Return:
        Updated HTML, Folder with downloaded images
    """
    # Extract any image URL from HTML and replace them with cid
    urls, html_cid = replace_image_urls_with_cid_in_html(html)
    # Create a folder using md5(html) as name and download images into it
    image_folder_name = hash_by_md5(html)
    image_folder_path = pathlib.Path(
        LOCAL_FOLDER).joinpath(image_folder_name)
    image_folder_path.mkdir(parents=True, exist_ok=True)
    for file_stem, url in urls.items():
        download_file_from_url(url, str(image_folder_path),
                               file_name=None, file_stem=file_stem)
    return html_cid, str(image_folder_path)


def find_and_replace_placeholders(text: str, replacements: Dict[str, str]) -> str:
    """
    Replace placeholders marked within {{}}
    """
    placeholders = find_placeholders_in_text(
        text, pattern='{{([a-zA-Z0-9_-]+)}}')
    dic = {f'{{{{{k}}}}}': replacements[k] for k in placeholders}
    return replace_all_substrings(text, dic)


def add_style_to_raw_html_table(html:str):
    styled_html = html.replace("<table>","<table cellspacing='3' cellpadding='3'>")
    styled_html = styled_html.replace("<th>","<th style='background-color: #3B3E50; color: #ffffff'>")
    styled_html = styled_html.replace("<td>","<td style='background-color: #ffffff'>")
    return styled_html

def process_email_task(payload: MailTaskType, configSetName: str = None) -> Dict:
    # Download image from any image URL from HTML and replace them with cid
    message_html_cid, image_folder_path = prepare_html_message_to_embed_images(
        payload.message_html)
    # Fill placeholders, which is surrounded by {{}}, in message_html with values from placeholders
    message_html_cid = find_and_replace_placeholders(
        message_html_cid, payload.placeholders)
    payload.message_text = find_and_replace_placeholders(
        payload.message_text, payload.placeholders)
    payload.subject = find_and_replace_placeholders(
        payload.subject, payload.placeholders)

    # Construct message
    msg = construct_email_from_content(payload.subject, payload.from_email, payload.to_emails,
                                       message_html_cid,
                                       payload.message_text,
                                       payload.reply_to_email)

    # Embedded images to message
    attach_local_images_to_email(msg, images_folder=image_folder_path)

    # Add attachments to message
    for key_prefix in payload.attachments:
        files = list_files_in_bucket(
            s3_client, payload.bucket_name, key_prefix)
        msg = attach_s3_files_to_email(
            msg, s3_client, payload.bucket_name, files)

    # Send Emails
    return send_raw_email(ses_client, msg, payload.from_email, to_emails=payload.to_emails, configSetName=configSetName)


def process_email_task_from_message_files(payload: MailTaskType, configSetName=None) -> Dict:
    if payload.message_html_key and not payload.message_html:
        # Download file from s3
        p = pathlib.Path(LOCAL_FOLDER).joinpath(
            payload.message_html_key)
        # Create folder if necessary
        p.parent.mkdir(parents=True, exist_ok=True)
        s3_client.download_file(payload.bucket_name,
                                payload.message_html_key, str(p))
        with open(str(p)) as f:
            payload.message_html = f.read()
    if payload.message_text_key and not payload.message_text:
        # Download file from s3
        p = pathlib.Path(LOCAL_FOLDER).joinpath(
            payload.message_text_key)
        # Create folder if necessary
        p.parent.mkdir(parents=True, exist_ok=True)
        s3_client.download_file(payload.bucket_name,
                                payload.message_text_key, str(p))
        with open(str(p)) as f:
            payload.message_text = f.read()
    return process_email_task(payload, configSetName)

def compose_ai_response_email(to_email: str,
                      placeholders: Dict,
                      from_email=ADMIN_EMAIL) -> MailTaskType:
    """
    Compose parts for an AI Response email
    """
    job = MailTaskType(to_emails=[to_email], from_email=from_email, subject='Your conversation on LaunchPad')
    job.placeholders = placeholders

    # The email body for recipients with non-HTML email clients.
    job.message_text = """AI Response:\r\n
    Your conversation:\n{{prompt}} \r\n\n\n
    The last response was:\n{{response}}.\r\n
    Requested at: {{created}}."""

    # The HTML body of the email.
    # job.message_html = """<html>
    # <head></head>
    # <body>
    #   <h2>AI Response:</h2>
    #   <p><b>Your conversation:</b><br/><pre>{{prompt}}</pre></p>
    #   <p><b>The last response was:</b><br/><pre>{{response}}</pre></p>
    #   <br/>
    #   <p>Requested at: {{created}}</p>
    # </body>
    # </html>
    # """

    template_folder = Path("app/common/email_template")

    header_html = (template_folder/"email_header.html").read_text()
    user_html = (template_folder/"user_template.html").read_text()
    ai_html = (template_folder/"ai_template.html").read_text()
    footer_html = (template_folder/"email_footer.html").read_text()

    job.message_html = header_html

    for msg in placeholders['messages']:
        msg_content = markdown.markdown(msg['content'],extensions=['tables'])
        msg_content = add_style_to_raw_html_table(msg_content)
        if msg['role'] == 'user':
            job.message_html += find_and_replace_placeholders(user_html,{'email':to_email,'prompt':msg_content})
        elif msg['role'] == 'assistant':
            job.message_html += find_and_replace_placeholders(ai_html,{'response':msg_content})

    response = markdown.markdown(placeholders['response'],extensions=['tables'])
    response = add_style_to_raw_html_table(response)
    job.message_html += find_and_replace_placeholders(ai_html,{'response':response})
    job.message_html += footer_html
    logger.info(f'message_html: {job.message_html}')

    logger.info(f'Composed AI Email: {job}')
    return job

if __name__ == "__main__":
    os.environ['AWS_PROFILE'] = 'capdev'
    session = boto3.session.Session(profile_name='capdev')
    s3_client = session.client('s3')
    ses_client = session.client('ses')
    sqs_client = session.client('sqs')

    bucket_name = 'blastoise-305326993135'

    subject = 'TD Background'
    from_email = '"CapDev DSAID" <data@tech.gov.sg>'
    reply_to_email = 'qinjie@dsaid.gov.sg'

    message_text = ''
    message_html = read_file_from_bucket(
        s3_client, bucket_name=bucket_name, key='test/html/thang_updated_2.html')

    email_task = {
        "subject": subject,
        "from_email": from_email,
        "reply_to_email": reply_to_email,
        'to_emails': ['mark.qj@gmail.com', 'qinjie@dsaid.gov.sg'],
        'attachments': ['test/pdf/chapter1.pdf', 'test/pdf/chapter2.pdf'],
        "placeholders": {
            'name': 'Mark Gmail',
            'greet': 'Good Weather today'},
        "message_text": message_text,
        "message_html": message_html,
        "bucket_name": bucket_name
    }

    queue_url = 'https://sqs.ap-southeast-1.amazonaws.com/305326993135/mail-postman-emails.fifo'
    sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(
        email_task), MessageGroupId='abc123')

    # process_email_task(s3_client, **email_task)

    email_task = {
        "subject": subject,
        "from_email": from_email,
        "reply_to_email": reply_to_email,
        'to_emails': ['zhang_qinjie@tech.gov.sg'],
        'attachments': ['test/pdf/chapter3.pdf', 'test/pdf/chapter4.pdf'],
        "placeholders": {
            'name': 'Mark Gmail',
            'greet': 'Good Weather today'},
        "message_text": "",
        "message_html": message_html,
        "bucket_name": bucket_name
    }

    sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(
        email_task), MessageGroupId='abc123')

    # process_email_task(s3_client, **email_task)
