import pathlib
from typing import Dict, List, Literal, Optional, Union
import uuid

from pydantic import BaseModel, EmailStr, NameEmail, validator


class MailTaskType(BaseModel):
    subject: str
    from_email: str
    to_emails: List[Union[EmailStr, NameEmail]]
    attachments: Optional[List[str]] = []
    reply_to_email: Optional[Union[EmailStr, NameEmail]] = ''
    cc_emails: Optional[List[str]] = []
    placeholders: Optional[Dict[str, str]] = {}
    message_text: Optional[str] = ''
    message_text_key: Optional[str] = ''
    message_html: Optional[str] = ''
    message_html_key: Optional[str] = ''
    bucket_name: Optional[str] = ''
    # For query purpose
    task_group: Optional[str]
    task_id: Optional[str]
    # For results
    task_status_name: Optional[str] = ''
    task_status_remark: Optional[str] = ''
    message_id: Optional[str] = None

    @validator('attachments', each_item=True)
    def validate_file_key_list(cls, v):
        try:
            if v:
                return pathlib.Path(v).as_posix()
            return v
        except Exception:
            raise ValueError(f'Key value must be a path: {v}')

    @validator('message_text_key', 'message_html_key')
    def validate_file_key(cls, v):
        try:
            if v:
                return pathlib.Path(v).as_posix()
            return v
        except Exception:
            raise ValueError(f'Key value must be a path: {v}')

    class Config:
        schema_extra = {
            "example": {
                "subject": "Hello From DSAID",
                "from_email": "CapDev DSAID <data@tech.gov.sg>",
                "to_emails": [
                    "qinjie@dsaid.gov.sg"
                ],
                "attachments": [
                    "test/pdf/chapter1.pdf",
                    "test/pdf/chapter2.pdf"
                ],
                "reply_to_email": "qinjie@dsaid.gov.sg",
                "cc_emails": [],
                "placeholders": {
                    "name": "Qinjie",
                    "message": "How are you?"
                },
                "message_text": "Hi{{name}}, {{message}}. Have a great day ahead\n\n Best regards, DSAID",
                "message_text_key": "",
                "message_html": "",
                "message_html_key": "",
                "bucket_name": "blastoise-305326993135",
            }
        }

MailTaskType.update_forward_refs()