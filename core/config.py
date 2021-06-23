import os

from dotenv import load_dotenv
from starlette.datastructures import CommaSeparatedStrings

load_dotenv(".env")

MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))

ALLOWED_HOSTS = CommaSeparatedStrings(os.getenv("ALLOWED_HOSTS", ""))

MONGODB_URI = os.getenv("MONGODB_URI")
users_collection_name = "users"
etsy_connections_collection_name = "EtsyShopConnections"
invitation_emails_collection_name = "InvitationEmails"
