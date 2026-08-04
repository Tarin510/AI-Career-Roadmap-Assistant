from database import test_connection

if test_connection():
    print("MongoDB Connected Successfully!")
else:
    print("MongoDB Connection Failed!")