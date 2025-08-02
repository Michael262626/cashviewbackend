from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List
from passlib.context import CryptContext
from services_db import get_user
from passlib.context import CryptContext
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_user(username: str, password: str):
    # Get the user from Supabase
    result = supabase.table("users").select("*").eq("username", username).execute()

    if not result.data:
        return None  # user not found

    user = result.data[0]

    # Verify password hash
    if not pwd_context.verify(password, user["password"]):
        return None

    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    from services_db import get_user as db_get_user
    user = await db_get_user(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user

def role_required(allowed_roles: List[str]):
    async def role_checker(user = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted for your role")
        return user
    return role_checker
