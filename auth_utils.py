import os 
from datetime import datetime, timedelta


from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60





pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _prehash(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()

def hash_password(password : str) -> str:
    return pwd_context.hash(_prehash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_prehash(plain_password), hashed_password)


def create_access_token(data : dict, expires_delta : timedelta = None) -> str:

    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token : str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms= ALGORITHM)
    except JWTError:
        return None
    
    