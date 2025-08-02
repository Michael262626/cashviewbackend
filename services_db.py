from datetime import datetime
from database import get_supabase_client

supabase = get_supabase_client()

async def create_refill_request(atm_id: str, requested_amount: float, requestor: str, comment: str = None):
    # Create the refill request
    data = {
        'atm_id': atm_id,
        'requested_amount': requested_amount,
        'requestor': requestor,
        'status': 'Pending',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    response = supabase.table('refillrequest').insert(data).execute()
    if response.error:
        raise Exception(f"Error creating refill request: {response.error.message}")
    new_request = response.data[0]

    # Create approval record if comment is provided
    if comment:
        approval_data = {
            'refill_request_id': new_request['request_id'],
            'approver': requestor,
            'role': 'ATM Operations Staff',
            'action': 'requested',
            'comment': comment,
            'timestamp': datetime.utcnow().isoformat()
        }
        approval_response = supabase.table('approvalrecord').insert(approval_data).execute()
        if approval_response.error:
            raise Exception(f"Error creating approval record: {approval_response.error.message}")

    return new_request

async def list_refill_requests(user_role: str, username: str, status_filter: str = None):
    # Build the query based on user role
    query = supabase.table('refillrequest')

    if user_role == "ATM Operations Staff":
        query = query.eq('requestor', username)
    elif user_role == "Branch Operations Manager":
        query = query.eq('status', 'Pending')
    elif user_role == "Vault Manager":
        query = query.eq('status', 'Approved')
    elif user_role == "Head Office Authorization Officer":
        # No filter for this role
        pass

    if status_filter:
        query = query.eq('status', status_filter)

    response = query.select('*, approval_history(*)').execute()
    if response.error:
        raise Exception(f"Error fetching refill requests: {response.error.message}")
    return response.data

async def take_action_on_refill_request(request_id: str, action: str, approver: str, role: str, comment: str = None):
    # Check if refill request exists
    response = supabase.table('refillrequest').select('*').eq('request_id', request_id).execute()
    if response.error:
        raise Exception(f"Error fetching refill request: {response.error.message}")
    refill_request = response.data[0] if response.data else None
    if not refill_request:
        raise ValueError("Refill request not found")
    if refill_request['status'] != "Pending":
        raise ValueError("Refill request already processed")
    if action.lower() not in ["approve", "refuse"]:
        raise ValueError("Invalid action")

    # Determine the new status based on action
    status = "Approved" if action.lower() == "approve" else "Refused" if action.lower() == "refuse" else "Pending"

    # Update the refill request status
    update_response = supabase.table('refillrequest').update({
        'status': status,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('request_id', request_id).execute()
    if update_response.error:
        raise Exception(f"Error updating refill request: {update_response.error.message}")

    # Create approval record
    approval_data = {
        'refill_request_id': request_id,
        'approver': approver,
        'role': role,
        'action': action.lower(),
        'comment': comment,
        'timestamp': datetime.utcnow().isoformat()
    }
    approval_response = supabase.table('approvalrecord').insert(approval_data).execute()
    if approval_response.error:
        raise Exception(f"Error creating approval record: {approval_response.error.message}")

    return update_response.data[0]

async def get_user(username: str):
    response = supabase.table('users').select('*').eq('username', username).execute()
    if response.error:
        raise Exception(f"Error fetching user: {response.error.message}")
    users = response.data
    if not users:
        return None
    return users[0]
