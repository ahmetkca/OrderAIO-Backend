"""
JWT in httpOnly cookies with OAuth2 password flow.
"""
from calendar import timegm
from datetime import datetime, timedelta

import jwt

from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

from schemas import UserData

from passlib.context import CryptContext
from config import JWT_SECRET

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class OAuth2PasswordCookie(OAuth2PasswordBearer):
	"""
	OAuth2 password flow with token in a httpOnly cookie.
    """
	
	def __init__(self, *args, token_name: str = None, **kwargs):
		super().__init__(*args, **kwargs)
		self._token_name = token_name or "my-jwt-token"
	
	@property
	def token_name(self) -> str:
		"""Get the name of the token's cookie.
        """
		return self._token_name
	
	async def __call__(self, request: Request) -> str:
		"""Extract and return a JWT from the request cookies.
        Raises:
            HTTPException: 403 error if no token cookie is present.
        """
		token = request.cookies.get(self._token_name)
		if not token:
			raise HTTPException(status_code=403, detail="Not authenticated")
		return token


oauth2_schema = OAuth2PasswordCookie(
	tokenUrl="/auth/token", scopes={"user": "User", "admin": "Admin"}
)


def validate_jwt_payload(token: str) -> dict:
	"""
	Decode and validate a JSON web token.

	Args:
		token (str): JWT token.

	Returns:
		dict

	Raises:
		HTTPException: 401 error if the credentials have expired or failed
			validation.
	"""
	
	try:
		payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
		print(payload)
		utc_now = timegm(datetime.utcnow().utctimetuple())
		print(payload["exp"])
		print(utc_now)
		if payload["exp"] <= utc_now:
			raise HTTPException(401, detail="Credentials have expired")
		return payload
	except jwt.PyJWTError:
		raise HTTPException(401, detail="Could not validate credentials")


def encode_token(**kwargs) -> str:
	"""
	Encode the given data to JSON web token
	
	Args:
		data = {
			'user': 'example-user'
			'user_id': 'user's id',
			'scopes': ['user', 'admin']
		}

	Returns:
		str (JSON web token)
	"""
	
	payload = {key: value for key, value in kwargs.items()}
	issued_at = datetime.utcnow()
	expire = issued_at + timedelta(minutes=15)
	payload.update({"exp": expire, "iat": issued_at, "sub": "jwt-cookies-test"})
	encoded_jwt = jwt.encode(
		payload,
		JWT_SECRET,
		algorithm="HS256"
	)
	return encoded_jwt


def is_authenticated(token: str = Security(oauth2_schema)) -> UserData:
	"""Dependency on user being authenticated.
	"""
	payload = validate_jwt_payload(token)
	return UserData(
		user=payload["user"], user_id=payload["user_id"], scopes=payload["scopes"]
	)


def get_password_hash(password):
	"""
	Hash the given plain password
	"""
	
	return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
	"""
	Verify the given plain_password to the given hashed_password (likely from database)
	"""
	
	return pwd_context.verify(plain_password, hashed_password)
