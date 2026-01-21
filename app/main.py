from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import create_db_and_tables
from app.routers import auth, accounts, categories, transactions, operations, dashboard

app = FastAPI(title="Personal Finance API", version="0.1.0")

# Ajustá CORS cuando tengas el dominio de la PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción poné tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(operations.router)
app.include_router(dashboard.router)

@app.get("/health")
def health():
    return {"status": "ok"}
