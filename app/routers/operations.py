from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import Account, Category, Transaction, User
from app.schemas import TransferCreate, CreditCardPaymentCreate
from app.deps import get_current_user

router = APIRouter(prefix="/operations", tags=["operations"])

@router.post("/transfer")
def transfer(
    payload: TransferCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(status_code=400, detail="from_account_id and to_account_id must differ")
    if payload.fee > 0 and not payload.fee_category_id:
        raise HTTPException(status_code=400, detail="fee_category_id required when fee > 0")

    a_from = session.get(Account, payload.from_account_id)
    a_to = session.get(Account, payload.to_account_id)
    if not a_from or a_from.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="From account not found")
    if not a_to or a_to.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="To account not found")

    if a_from.type == "credit_card" or a_to.type == "credit_card":
        raise HTTPException(status_code=400, detail="Transfers only allowed between bank/cash accounts")

    group_id = uuid4()

    tx_out = Transaction(
        user_id=current_user.id,
        account_id=a_from.id,
        type="transfer_out",
        payment_method=payload.payment_method,
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        description=payload.description,
        group_id=group_id
    )
    tx_in = Transaction(
        user_id=current_user.id,
        account_id=a_to.id,
        type="transfer_in",
        payment_method=payload.payment_method,
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        description=payload.description,
        group_id=group_id
    )

    session.add(tx_out)
    session.add(tx_in)

    created = [{"type":"transfer_out"}, {"type":"transfer_in"}]

    if payload.fee and payload.fee > 0:
        fee_cat = session.get(Category, payload.fee_category_id)
        if not fee_cat or fee_cat.user_id != current_user.id or fee_cat.type != "expense":
            raise HTTPException(status_code=400, detail="Invalid fee_category_id")

        tx_fee = Transaction(
            user_id=current_user.id,
            account_id=a_from.id,
            category_id=fee_cat.id,
            type="expense",
            payment_method=payload.payment_method,
            amount=payload.fee,
            transaction_date=payload.transaction_date,
            description="Fee: " + (payload.description or "transfer"),
            group_id=group_id
        )
        session.add(tx_fee)
        created.append({"type":"expense", "note":"fee"})

    session.commit()
    return {"group_id": str(group_id), "created": created}


@router.post("/credit-card-payment")
def credit_card_payment(
    payload: CreditCardPaymentCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if payload.fee > 0 and not payload.fee_category_id:
        raise HTTPException(status_code=400, detail="fee_category_id required when fee > 0")

    bank = session.get(Account, payload.bank_account_id)
    card = session.get(Account, payload.credit_card_account_id)
    if not bank or bank.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bank account not found")
    if not card or card.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Credit card account not found")

    if bank.type not in ("bank", "cash"):
        raise HTTPException(status_code=400, detail="bank_account_id must be bank/cash")
    if card.type != "credit_card":
        raise HTTPException(status_code=400, detail="credit_card_account_id must be credit_card")

    pay_cat = session.get(Category, payload.payment_category_id)
    if not pay_cat or pay_cat.user_id != current_user.id or pay_cat.type != "expense":
        raise HTTPException(status_code=400, detail="Invalid payment_category_id (must be expense)")

    group_id = uuid4()

    # A) sale dinero del banco (categoría Pago tarjeta)
    tx_bank = Transaction(
        user_id=current_user.id,
        account_id=bank.id,
        category_id=pay_cat.id,
        type="expense",
        payment_method=payload.payment_method,
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        description=payload.description or f"Credit card payment ({payload.reference or ''})".strip(),
        group_id=group_id
    )

    # B) abono a la tarjeta (reduce deuda)
    tx_card = Transaction(
        user_id=current_user.id,
        account_id=card.id,
        type="credit_payment",
        payment_method=payload.payment_method,
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        description=payload.description or "Credit card payment",
        group_id=group_id
    )

    session.add(tx_bank)
    session.add(tx_card)

    created = [{"type":"expense","note":"bank_out"}, {"type":"credit_payment","note":"card_in"}]

    # C) comisión opcional (gasto real)
    if payload.fee and payload.fee > 0:
        fee_cat = session.get(Category, payload.fee_category_id)
        if not fee_cat or fee_cat.user_id != current_user.id or fee_cat.type != "expense":
            raise HTTPException(status_code=400, detail="Invalid fee_category_id")

        tx_fee = Transaction(
            user_id=current_user.id,
            account_id=bank.id,
            category_id=fee_cat.id,
            type="expense",
            payment_method=payload.payment_method,
            amount=payload.fee,
            transaction_date=payload.transaction_date,
            description="Fee: " + (payload.description or "card payment"),
            group_id=group_id
        )
        session.add(tx_fee)
        created.append({"type":"expense","note":"fee"})

    session.commit()
    return {"group_id": str(group_id), "created": created}
