import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGO_URI)

db = client[os.getenv("DATABASE_NAME")]

# Collections
users_collection = db["users"]
sessions_collection = db["sessions"]
analyses_collection = db["analyses"]


def test_connection():
    try:
        client.admin.command("ping")
        return True
    except Exception as e:
        print(e)
        return False