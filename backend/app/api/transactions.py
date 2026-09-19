"""
Transaction API routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
)
from app.services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    get_transactions,
    update_transaction,
    delete_transaction,
    get_or_create_default_user,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create_new_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    """Create a new transaction."""
    user = get_or_create_default_user(db)
    txn = create_transaction(
        db=db,
        user_id=user.id,
        amount=data.amount,
        transaction_type=data.transaction_type,
        category=data.category,
        description=data.description,
        transaction_date=data.transaction_date,
    )
    return txn


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """Get paginated transaction list with optional filters."""
    user = get_or_create_default_user(db)
    transactions, total = get_transactions(
        db=db,
        user_id=user.id,
        page=page,
        page_size=page_size,
        category=category,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
    )
    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_single_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Get a single transaction by ID."""
    txn = get_transaction_by_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_existing_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing transaction."""
    update_data = data.model_dump(exclude_unset=True)
    txn = update_transaction(db, transaction_id, **update_data)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.delete("/{transaction_id}", status_code=204)
def delete_existing_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Delete a transaction."""
    success = delete_transaction(db, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None
