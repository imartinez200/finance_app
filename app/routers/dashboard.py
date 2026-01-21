from datetime import date
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Account, Transaction, User
from app.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/monthly")
def monthly(year: int, month: int,
            current_user: User = Depends(get_current_user),
            session: Session = Depends(get_session)):
    # rango de fechas del mes
    start = date(year, month, 1)
    end = date(year + (month // 12), (month % 12) + 1, 1)

    txs = session.exec(select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date >= start,
        Transaction.transaction_date < end
    )).all()

    # ingresos (solo bank/cash)
    accounts = session.exec(select(Account).where(Account.user_id == current_user.id)).all()
    acc_type = {a.id: a.type for a in accounts}

    income = sum(t.amount for t in txs if t.type == "income" and acc_type.get(t.account_id) in ("bank","cash"))

    # gastos "consumo real": expense en bank/cash y en credit_card,
    # pero OJO: en el frontend podés excluir la categoría "Pago tarjeta" en reportes si querés
    expense = sum(t.amount for t in txs if t.type == "expense" and acc_type.get(t.account_id) in ("bank","cash","credit_card"))

    balance = income - expense

    return {"period": {"year": year, "month": month}, "income": income, "expense": expense, "balance": balance}
