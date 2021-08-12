from enum import Enum
from typing import List
from pydantic import BaseModel


class ReceiptStatus(str, Enum):
    OPEN: str = "open"
    UNSHIPPED: str = "unshipped"
    UNPAID: str = "unpaid"
    COMPLETED: str = "completed"
    PROCESSING: str = "processing"
    ALL: str = "all"


class NoteUpdate(BaseModel):
    note: str


class NoteData(BaseModel):
    receipt_id: str
    note: str


class UserData(BaseModel):
    """
        user = Username (username1, username2 etc.) 
        user_id = User_id (60cd51a2a44682438f29307e etc.)
        scopes= scopes (admin, guest etc.)
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
