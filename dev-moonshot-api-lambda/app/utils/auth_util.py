import datetime
from random import randint
from uuid import uuid4

import jwt
from fastapi import HTTPException

from app.config import JWT_VALID_HOURS

JWT_SECRET = 'this is a secret'
OTP_DIGITS = 4


def gen_otp(digits=OTP_DIGITS):
    """
    Return an integer digits in string as OTP
    """
    number = randint(1, 10 ** digits)
    return f'{number:0{digits}d}'


def pad_int(number, digits=OTP_DIGITS):
    """
    Convert an integer into a string with leading 0 padding
    """
    return f'{number:0{digits}d}'


def gen_jwt_token(payload_data, jwt_secret=JWT_SECRET, valid_hours=JWT_VALID_HOURS):
    """
    Generate a JWT Token with payload_data
    """
    now = datetime.datetime.utcnow()
    unique_id = str(uuid4())
    payload = {
        'sub': payload_data,
        'iat': now,
        'jti': unique_id,
    }
    if valid_hours and valid_hours > 0:
        payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=valid_hours)

    return jwt.encode(payload, jwt_secret, algorithm='HS256')


def decode_jwt_token(jwt_token, jwt_secret=JWT_SECRET):
    """
    Decode a JWT Token and return its data
    """
    try:
        return jwt.decode(jwt_token, jwt_secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        print("Exception: Token expired. Get new one")
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        print("Exception: Invalid Token")
        raise HTTPException(status_code=401, detail='Invalid token')


def check_token_permission(jwt_token, app_label=None):
    """Decode JWT and check permissions
     param jwt_token: JWT token must include permissions field which has list of apps user is authorized
     param app_label: if app_label is empty, no need to check whether user has rights to the app, or the app is public
     return: data extracted from JWT
     """
    jwt_data = decode_jwt_token(jwt_token)
    # jwt_sub = json.loads(jwt_data['sub'])
    jwt_sub = jwt_data['sub']

    if 'permissions' not in jwt_sub.keys():
        raise HTTPException(status_code=400, detail=f'Invalid token format: Token has no "permission" field.')
    if app_label and app_label not in jwt_sub['permissions']:
        raise HTTPException(status_code=403, detail=f'You are not permitted to use module "{app_label}"')

    return jwt_sub


if __name__ == '__main__':
    token = gen_jwt_token({'message': 'Hello World'}, JWT_SECRET)
    print(token)
    data = decode_jwt_token(token, JWT_SECRET)
    print(data)
