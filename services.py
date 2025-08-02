from typing import List, Optional
from datetime import datetime
from models import RefillRequest, ApprovalRecord
from services_db import create_refill_request as db_create_refill_request, list_refill_requests as db_list_refill_requests, take_action_on_refill_request as db_take_action_on_refill_request

async def create_refill_request(atm_id: str, requested_amount: float, requestor: str, comment: str = None) -> RefillRequest:
    """
    Create a new refill request
    """
    new_request_db = await db_create_refill_request(atm_id, requested_amount, requestor, comment)
    
    # Convert to RefillRequest object
    return RefillRequest(
        request_id=new_request_db['request_id'],
        atm_id=new_request_db['atm_id'],
        requested_amount=new_request_db['requested_amount'],
        requestor=new_request_db['requestor'],
        status=new_request_db['status'],
        created_at=new_request_db['created_at'],
        updated_at=new_request_db['updated_at'],
        approval_history=[]  # Will be populated when needed
    )

async def list_refill_requests(user_role: str, username: str, status_filter: str = None) -> List[RefillRequest]:
    """
    List refill requests
    """
    requests_db = await db_list_refill_requests(user_role, username, status_filter)
    
    # Convert to RefillRequest objects
    result = []
    for r in requests_db:
        approval_history = [
            ApprovalRecord(
                approver=record['approver'],
                role=record['role'],
                action=record['action'],
                timestamp=record['timestamp'],
                comment=record.get('comment')
            ) for record in r.get('approval_history', [])
        ]
        result.append(
            RefillRequest(
                request_id=r['request_id'],
                atm_id=r['atm_id'],
                requested_amount=r['requested_amount'],
                requestor=r['requestor'],
                status=r['status'],
                created_at=r['created_at'],
                updated_at=r['updated_at'],
                approval_history=approval_history
            )
        )
    return result

async def take_action_on_refill_request(request_id: str, action: str, approver: str, role: str, comment: str = None) -> RefillRequest:
    """
    Take action on a refill request
    """
    updated_request_db = await db_take_action_on_refill_request(request_id, action, approver, role, comment)
    
    # Get the complete request with approval history
    requests_db = await db_list_refill_requests(role, approver, None)
    complete_request_db = next((r for r in requests_db if r['request_id'] == request_id), None)
    
    if not complete_request_db:
        raise ValueError("Refill request not found")
    
    # Convert to RefillRequest object
    approval_history = [
        ApprovalRecord(
            approver=record['approver'],
            role=record['role'],
            action=record['action'],
            timestamp=record['timestamp'],
            comment=record.get('comment')
        ) for record in complete_request_db.get('approval_history', [])
    ]
    
    return RefillRequest(
        request_id=complete_request_db['request_id'],
        atm_id=complete_request_db['atm_id'],
        requested_amount=complete_request_db['requested_amount'],
        requestor=complete_request_db['requestor'],
        status=complete_request_db['status'],
        created_at=complete_request_db['created_at'],
        updated_at=complete_request_db['updated_at'],
        approval_history=approval_history
    )
