from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine
from sqlalchemy import func
import models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ['http://localhost:3000' ,]  # port/ diff app is allowed to call fastapi only through port 3000

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# pydantic model , which validated requests from react, based on data is valid we accept or reject
class TransactionBase(BaseModel):
    amount: float
    category: str
    description: str
    is_income: bool
    date: str

# It defines what information the client (frontend) is allowed to send and receive
class TransactionModel(TransactionBase):
    id: int

    class Config:
        orm_mode = True


# frontend -> backend
class UserBase(BaseModel):
    email: str
    password: str

# backend -> frontend 
class UserModel(BaseModel):
    id: int
    email: str

    # connect SQLAlchemy models (database) with Pydantic models (schemas)
    class Config:
        orm_mode = True

def get_db():
    '''dependency injection for the app'''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# This uses dependency injection, meaning FastAPI handles creating and closing the connection for me
db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)

# @ Route decorator
@app.post("/transactions/", response_model=TransactionModel)
async def create_transaction(transaction: TransactionBase, db: db_dependency):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction
# ------------------------------------------------------------------------------

@app.get("/transactions/", response_model=List[TransactionModel])
async def read_transactions(db: db_dependency, skip: int = 0, limit: int = 100):
    transactions = db.query(models.Transaction).offset(skip).limit(limit).all()

    return transactions
# ------------------------------------------------------------------------------

@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id, db: db_dependency):
    # Find the transaction in the DB
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Delete and commit
    db.delete(transaction)
    db.commit()
    return {"message": f"Transaction {transaction_id} deleted successfully"}

# ------------------------------------------------------------------------------

@app.put("/transactions/")
async def update_transaction(transaction_id: int, transaction: TransactionBase, db: db_dependency):
    transact_to_update = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if transact_to_update is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in transaction.dict().items():
        setattr(transact_to_update, key, value)  # update each field

    # or i can do it manually (old version)
    #db_transaction.amount = transaction.amount
    #db_transaction.category = transaction.category
    #db_transaction.description = transaction.description
    #db_transaction.is_income = transaction.is_income
    #db_transaction.date = transaction.date

    db.commit()
    db.refresh(transact_to_update)

    return transact_to_update

# ------------------------------------------------------------------------------

@app.get("/summary/")
async def get_summary(db: db_dependency):
    income = db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.is_income == True).scalar() or 0
    expense = db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.is_income == False).scalar() or 0
    balance = income - expense
    return {"income": income, "expense": expense, "balance": balance}

# ------------------------------------------------------------------------------


@app.post("/users/", response_model=UserModel)
async def create_users( user: UserBase, db: db_dependency):
    #creates a new SQLAlchemy model object (row) that matches User table. (“Take the email and password from the frontend and prepare them for database insertion.”)
    db_user = models.User(email = user.email, hashed_password = user.password)
    # Adds it to the database session
    db.add(db_user)
    # Actually saves it in the database file
    db.commit()
    # Reloads that db_user object from the database
    db.refresh(db_user)
    #Returns the newly created user to the frontend.
    return db_user
