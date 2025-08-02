from fastapi import FastAPI, Body, HTTPException, Query, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from typing import Optional, List
from pydantic import BaseModel
import warnings
import traceback
import uuid
from datetime import datetime
from supabase import create_client
import os

# ====================== SUPABASE SETUP ======================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ruzsihysifzxdxbvrmlc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1enNpaHlzaWZ6eGR4YnZybWxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQwNTkzNjMsImV4cCI6MjA2OTYzNTM2M30.MiN9jDHeDv9lv6wm1X-jtrZTxkhUQWQqtQIjP-0b0a8")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

warnings.filterwarnings("ignore")

app = FastAPI()

# ✅ CORS setup for your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://cashprediction-orpin.vercel.app"],  # your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== AUTH HELPERS ======================
async def authenticate_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if res.user:
            return {"email": res.user.email, "role": "ATM Operations Staff"}
        else:
            print("Supabase login failed:", res)
            return None
    except Exception as e:
        print("Auth error:", e)
        return None


def get_current_user(token: str = Depends(OAuth2PasswordRequestForm)):
    # You can replace this with Supabase JWT verification if using full auth
    return {"username": token.username, "role": "ATM Operations Staff"}

def role_required(roles: list):
    def wrapper(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        return user
    return wrapper

# ====================== Pydantic Schemas ======================
class ApprovalRecord(BaseModel):
    approver: str
    action: str
    comment: Optional[str] = None
    timestamp: str
    class Config:
        orm_mode = True

class CreateUser(BaseModel):
    username: str
    email: str
    password: str
    role: str = "ATM Operations Staff"

class RefillRequest(BaseModel):
    request_id: str
    atm_id: str
    requested_amount: float
    requestor: str
    status: str
    comment: Optional[str] = None
    approval_history: Optional[List[ApprovalRecord]] = None
    class Config:
        orm_mode = True

class RefillRequestCreate(BaseModel):
    atm_id: str
    requested_amount: float
    comment: Optional[str] = None

class RefillRequestAction(BaseModel):
    action: str  # "approve" or "refuse"
    comment: Optional[str] = None

# ====================== SERVICES ======================
async def create_refill_request(atm_id, requested_amount, requestor, comment=None):
    request_id = str(uuid.uuid4())
    data = {
        "request_id": request_id,
        "atm_id": atm_id,
        "requested_amount": requested_amount,
        "requestor": requestor,
        "status": "Pending",
        "comment": comment,
        "created_at": datetime.utcnow().isoformat()
    }
    response = supabase.table("refill_requests").insert(data).execute()
    if response.error:
        raise Exception(response.error.message)
    return data

async def list_refill_requests(user_role, username, status_filter=None):
    query = supabase.table("refill_requests").select("*")
    if user_role not in ["Branch Operations Manager", "Head Office Authorization Officer", "Vault Manager"]:
        query = query.eq("requestor", username)
    if status_filter:
        query = query.eq("status", status_filter)
    response = query.execute()
    if response.error:
        raise Exception(response.error.message)
    return response.data

async def take_action_on_refill_request(request_id, action, approver, role, comment=None):
    response = supabase.table("refill_requests").update({
        "status": "Approved" if action.lower() == "approve" else "Refused",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("request_id", request_id).execute()
    if response.error:
        raise Exception(response.error.message)

    supabase.table("approval_history").insert({
        "request_id": request_id,
        "approver": approver,
        "action": action.capitalize(),
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat(),
        "role": role
    }).execute()

    return response.data[0]

@app.post("/api/v1/token")
async def login(request: Request):
    body = await request.json()
    print("Raw request body:", body)

    email = body.get("email")
    password = body.get("password")

    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    return {"access_token": user["email"], "token_type": "bearer"}


@app.post("/api/v1/users")
async def create_user(
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    role: str = Body("ATM Operations Staff")
):
    try:
        # Hash the password before saving
        hashed_password = pwd_context.hash(password)

        # Insert into Supabase
        result = supabase.table("users").insert({
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()

        if result.data:
            return {"message": "User created successfully", "user": result.data[0]}
        else:
            return {"error": "Failed to create user", "details": result}

    except Exception as e:
        return {"error": str(e)}

# ====================== REFILL REQUESTS ======================
refill_router = APIRouter()

@refill_router.post("/api/v1/refill-requests/", status_code=201)
async def create_refill_request_endpoint(
    request_data: RefillRequestCreate,
    user: dict = Depends(role_required(["ATM Operations Staff"]))
):
    new_request = await create_refill_request(
        atm_id=request_data.atm_id,
        requested_amount=request_data.requested_amount,
        requestor=user["username"],
        comment=request_data.comment
    )
    return {"message": "Refill request created", "request_id": new_request["request_id"]}

@refill_router.get("/api/v1/refill-requests/", response_model=List[RefillRequest])
async def list_refill_requests_endpoint(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    user: dict = Depends(get_current_user)
):
    filtered = await list_refill_requests(
        user_role=user["role"],
        username=user["username"],
        status_filter=status_filter
    )
    return filtered

@refill_router.post("/api/v1/refill-requests/{request_id}/action")
async def take_action_on_refill_request_endpoint(
    request_id: str,
    action_data: RefillRequestAction,
    user: dict = Depends(role_required([
        "Branch Operations Manager", "Head Office Authorization Officer"
    ]))
):
    try:
        updated_request = await take_action_on_refill_request(
            request_id=request_id,
            action=action_data.action,
            approver=user["username"],
            role=user["role"],
            comment=action_data.comment
        )
        return {"message": f"Refill request {updated_request['status'].lower()}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@refill_router.get("/api/v1/refill-requests/{request_id}/audit", response_model=List[ApprovalRecord])
async def get_refill_request_audit_endpoint(
    request_id: str,
    user: dict = Depends(get_current_user)
):
    filtered = await list_refill_requests(
        user_role=user["role"],
        username=user["username"],
        status_filter=None
    )
    refill_request = next(
        (r for r in filtered if r["request_id"] == request_id),
        None
    )
    if not refill_request:
        raise HTTPException(status_code=404, detail="Refill request not found")
    if user["role"] not in ["Branch Operations Manager", "Head Office Authorization Officer", "Vault Manager"] \
       and user["username"] != refill_request["requestor"]:
        raise HTTPException(status_code=403, detail="Not authorized to view audit trail")

    history_res = supabase.table("approval_history").select("*").eq("request_id", request_id).execute()
    return history_res.data

app.include_router(refill_router)
