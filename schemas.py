from typing import List
from pydantic import BaseModel


class UserData(BaseModel):
    """User name, ID and scopes
    """

    user: str
    user_id: str
    scopes: List[str]

# class InvitationDetails(BaseModel):
#     email: EmailStr


# class RegisterDetails(BaseModel):
#     email: EmailStr
#     username: str
#     password: str
#     verification_code: str


# class AuthDetails(BaseModel):
#     email: EmailStr
#     username: str
#     password: str
