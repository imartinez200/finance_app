from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, text, DateTime


class AccountType(str, Enum):
    bank = "bank"
    cash = "cash"
    credit_card = "credit_card"


class CategoryType(str, Enum):
    income = "income"
    expense = "expense"


class TxType(str, Enum):
    income = "income"
    expense = "expense"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"
    credit_payment = "credit_payment"


class PayMethod(str, Enum):
    cash = "cash"
    card = "card"
    sinpe = "sinpe"
    bank_transfer = "bank_transfer"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    email: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False)
    )

    password_hash: str
    currency: str = Field(default="CRC", max_length=3)

    created_at: datetime = Field(
        sa_column=Column(nullable=False, server_default=text("now()"))
    )

    accounts: list["Account"] = Relationship(back_populates="user")
    categories: list["Category"] = Relationship(back_populates="user")
    transactions: list["Transaction"] = Relationship(back_populates="user")


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    name: str = Field(index=True)
    type: AccountType = Field(index=True)
    initial_balance: float = Field(default=0.0)
    active: bool = Field(default=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    )

    user: "User" = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    name: str = Field(index=True)
    type: CategoryType = Field(index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    )

    user: "User" = Relationship(back_populates="categories")


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    account_id: UUID = Field(foreign_key="accounts.id", index=True)
    category_id: Optional[UUID] = Field(default=None, foreign_key="categories.id", index=True)

    type: TxType = Field(index=True)
    payment_method: Optional[PayMethod] = Field(default=None, index=True)

    amount: float = Field(gt=0)
    transaction_date: date = Field(index=True)

    description: Optional[str] = None
    counterparty: Optional[str] = Field(default=None, index=True)

    group_id: Optional[UUID] = Field(default=None, index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    )

    user: "User" = Relationship(back_populates="transactions")
    account: "Account" = Relationship(back_populates="transactions")
