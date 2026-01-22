from datetime import date
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

AccountType = Literal["bank", "cash", "credit_card"]
CategoryType = Literal["income", "expense"]
TxType = Literal["income", "expense", "transfer_in", "transfer_out", "credit_payment"]
PayMethod = Literal["cash", "card", "sinpe", "bank_transfer"]

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    currency: str

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AccountCreate(BaseModel):
    name: str
    type: AccountType
    initial_balance: float = 0.0

class AccountPatch(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    initial_balance: Optional[float] = None

class CategoryCreate(BaseModel):
    name: str
    type: CategoryType

class TransactionCreate(BaseModel):
    account_id: UUID
    category_id: Optional[UUID] = None
    type: TxType
    payment_method: Optional[PayMethod] = None
    amount: float
    transaction_date: date
    description: Optional[str] = None
    counterparty: Optional[str] = None

class TransferCreate(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    amount: float
    transaction_date: date
    payment_method: PayMethod = "bank_transfer"
    fee: float = 0.0
    fee_category_id: Optional[UUID] = None
    description: Optional[str] = None

class CreditCardPaymentCreate(BaseModel):
    bank_account_id: UUID
    credit_card_account_id: UUID
    amount: float
    transaction_date: date
    payment_method: PayMethod = "sinpe"
    payment_category_id: UUID
    fee: float = 0.0
    fee_category_id: Optional[UUID] = None
    reference: Optional[str] = None
    description: Optional[str] = None
