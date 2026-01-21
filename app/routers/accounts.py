from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Account, User, Transaction
from app.schemas import AccountCreate, AccountPatch
from app.deps import get_current_user

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("")
def list_accounts(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    accounts = session.exec(select(Account).where(Account.user_id == current_user.id)).all()
    return accounts

@router.post("")
def create_account(
    payload: AccountCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    acc = Account(user_id=current_user.id, name=payload.name, type=payload.type, initial_balance=payload.initial_balance)
    session.add(acc)
    session.commit()
    session.refresh(acc)
    return acc

@router.patch("/{account_id}")
def patch_account(
    account_id: str,
    payload: AccountPatch,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    acc = session.get(Account, account_id)
    if not acc or acc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    if payload.name is not None:
        acc.name = payload.name
    if payload.active is not None:
        acc.active = payload.active
    if payload.initial_balance is not None:
        acc.initial_balance = payload.initial_balance

    session.add(acc)
    session.commit()
    session.refresh(acc)
    return acc

@router.get("/{account_id}/balance")
def account_balance(
    account_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    acc = session.get(Account, account_id)
    if not acc or acc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    txs = session.exec(select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.account_id == acc.id
    )).all()

    if acc.type in ("bank", "cash"):
        income = sum(t.amount for t in txs if t.type == "income")
        tin = sum(t.amount for t in txs if t.type == "transfer_in")
        expense = sum(t.amount for t in txs if t.type == "expense")
        tout = sum(t.amount for t in txs if t.type == "transfer_out")
        balance = float(acc.initial_balance + income + tin - expense - tout)
        return {"account_id": str(acc.id), "type": acc.type, "balance": balance}

    # credit card debt
    spend = sum(t.amount for t in txs if t.type == "expense")
    paid = sum(t.amount for t in txs if t.type == "credit_payment")
    debt = float(acc.initial_balance + spend - paid)
    return {"account_id": str(acc.id), "type": acc.type, "debt": debt}
