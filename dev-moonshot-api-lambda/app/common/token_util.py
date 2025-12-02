import base64
from typing import Tuple

from app.config import (VALUE_DELIMITOR)
from app.utils.re_util import validate_email_address


def decode_optout_token(encoded_campaign_email: str) -> Tuple[str, str]:
    """
    Decode encoded param to get campaign_id and email, which will be used to opt-out/in an email
    """
    campaign_email = base64.b64decode(
        encoded_campaign_email).decode("utf-8")
    campaign_id, email = campaign_email.split(VALUE_DELIMITOR)
    if not validate_email_address(email):
        raise Exception(f'Invalid email address: {email}')
    return campaign_id, email


def encode_optout_token(campaign_id: str, email: str) -> str:
    """
    Encode campaign_id and email into an optout param, which can be used to opt-out/in an email
    """
    return base64.b64encode(str.encode(f'{campaign_id}{VALUE_DELIMITOR}{email}')).decode("utf-8")
