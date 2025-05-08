import os

SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30