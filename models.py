from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ApprovalRecord(BaseModel):
    approver: str
    role: str
    action: str
    timestamp: datetime
    comment: Optional[str] = None

    class Config:
        orm_mode = True

class RefillRequest(BaseModel):
    request_id: str
    atm_id: str
    requested_amount: float
    requestor: str
    status: str
    created_at: datetime
    updated_at: datetime
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

class User(BaseModel):
    username: str
    role: str

    class Config:
        orm_mode = True
