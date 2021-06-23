from typing import List
from pydantic import BaseModel


class NoteUpdate(BaseModel):
    note: str


class NoteData(BaseModel):
    receipt_id: str
    note: str


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
