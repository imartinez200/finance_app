from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Transaction, Account, Category, User
from app.schemas import TransactionCreate
from app.deps import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("")
def list_transactions(
    from_date: str | None = None,
    to_date: str | None = None,
    account_id: str | None = None,
    category_id: str | None = None,
    payment_method: str | None = None,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    if from_date:
        query = query.where(Transaction.transaction_date >= from_date)
    if to_date:
        query = query.where(Transaction.transaction_date <= to_date)
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if payment_method:
        query = query.where(Transaction.payment_method == payment_method)
    if q:
        query = query.where(Transaction.description.contains(q) | Transaction.counterparty.contains(q))
    query = query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
    return session.exec(query).all()

@router.post("")
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    acc = session.get(Account, payload.account_id)
    if not acc or acc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    # Validaciones por tipo de cuenta
    if acc.type in ("bank", "cash"):
        if payload.type == "credit_payment":
            raise HTTPException(status_code=400, detail="credit_payment is only for credit cards")
        if payload.type in ("transfer_in", "transfer_out"):
            raise HTTPException(status_code=400, detail="Use /operations/transfer for transfers")
    else:  # credit_card
        if payload.type not in ("expense", "credit_payment"):
            raise HTTPException(status_code=400, detail="Credit cards only allow expense or credit_payment")
        if payload.type == "credit_payment" and payload.category_id is not None:
            # opcional: forzamos category_id null en credit_payment
            pass

    if payload.category_id:
        cat = session.get(Category, payload.category_id)
        if not cat or cat.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Category not found")

    tx = Transaction(
        user_id=current_user.id,
        account_id=acc.id,
        category_id=payload.category_id,
        type=payload.type,
        payment_method=payload.payment_method,
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        description=payload.description,
        counterparty=payload.counterparty,
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx
