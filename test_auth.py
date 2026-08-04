from auth import register_user, login_user

# Register a test user
success, message = register_user(
    "Mahia",
    "mahia@gmail.com",
    "123456"
)

print(message)

# Test login
user = login_user(
    "mahia@gmail.com",
    "123456"
)

if user:
    print("Login Successful!")
    print(user)
else:
    print("Login Failed!")