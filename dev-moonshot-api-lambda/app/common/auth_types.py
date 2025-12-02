from typing import List, Optional, Union

from pydantic import BaseModel, EmailStr, validator, NameEmail


class EmailType(BaseModel):
    email: Union[EmailStr, NameEmail]
    ip: Optional[str]
    app: Optional[str]

    @validator('email')
    def validate_email(cls, v):
        """
        Convert email to lower case and check validity of the email.
        """
        v = v.lower()
        return v

    class Config:
        schema_extra = {
            "example": {
                "email": 'gvinto@gmail.com'
            }
        }


class EmailOtpType(BaseModel):
    email: EmailStr
    otp: str
    otp_expire: Optional[str]
    jwt: Optional[str]
    name: Optional[str]
    role: Optional[str]
    permissions: Optional[List]
    created_at: Optional[str]
    updated_at: Optional[str]

    @validator('email')
    def validate_email(cls, v):
        """
        Convert email to lower case
        """
        v = v.lower()
        return v

    class Config:
        schema_extra = {
            "example": {
                "email": "gvinto@gmail.com",
                "otp": "1234"
            }
        }


class JwtType(BaseModel):
    email: EmailStr
    role: Optional[str] = 'public'
    permissions: Optional[List[str]] = []
    name: Optional[str] = ''
