import os

CLIENT_HOST = os.getenv("CLIENT_HOST", "0.0.0.0")
CLIENT_PORT = os.getenv("CLIENT_PORT", 1759)

ADMIN_HOST = os.getenv("ADMIN_HOST", "0.0.0.0")
ADMIN_PORT = os.getenv("ADMIN_PORT", 1800)

SECRET_KEY = os.getenv("SECRET_KEY", "25688b47285b376f8599021643c37dcbf7a4e699d2f1c2c2c02a153e8664713f")
