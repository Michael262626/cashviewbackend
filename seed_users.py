from supabase import create_client
import os
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ruzsihysifzxdxbvrmlc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1enNpaHlzaWZ6eGR4YnZybWxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQwNTkzNjMsImV4cCI6MjA2OTYzNTM2M30.MiN9jDHeDv9lv6wm1X-jtrZTxkhUQWQqtQIjP-0b0a8")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

users = [
    {
        "id": str(uuid.uuid4()),
        "username": "atm_staff",
        "email": "atm_staff@example.com",
        "password": pwd_context.hash("password123"),  # hash before storing
        "role": "ATM Operations Staff",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "username": "branch_manager",
        "email": "branch_manager@example.com",
        "password": pwd_context.hash("password123"),
        "role": "Branch Operations Manager",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "username": "head_officer",
        "email": "head_officer@example.com",
        "password": pwd_context.hash("password123"),
        "role": "Head Office Authorization Officer",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]

try:
    res = supabase.table("users").upsert(users, on_conflict="username").execute()
    print("✅ Seeded users:", res.data)
except Exception as e:
    print("❌ Error seeding users:", e)
