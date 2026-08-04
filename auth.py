import secrets
import bcrypt
from bson import ObjectId

from database import users_collection, sessions_collection


# -----------------------------
# Register New User
# -----------------------------
def register_user(full_name, email, password):

    existing_user = users_collection.find_one({"email": email})

    if existing_user:
        return False, "Email already exists."

    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    users_collection.insert_one({
        "full_name": full_name,
        "email": email,
        "password": hashed_password
    })

    return True, "Registration Successful."


# -----------------------------
# Login User
# -----------------------------
def login_user(email, password):

    user = users_collection.find_one({"email": email})

    if user is None:
        return None

    if bcrypt.checkpw(
        password.encode("utf-8"),
        user["password"].encode("utf-8")
    ):
        return user

    return None


# -----------------------------
# Session Tokens
# -----------------------------
def create_session(user_id):

    token = secrets.token_urlsafe(32)

    sessions_collection.insert_one({
        "token": token,
        "user_id": str(user_id)
    })

    return token


def get_user_by_session(token):

    session = sessions_collection.find_one({"token": token})

    if session is None:
        return None

    user = users_collection.find_one({
        "_id": ObjectId(session["user_id"])
    })

    return user


def delete_session(token):

    sessions_collection.delete_one({"token": token})