from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.deps import get_db

router = APIRouter()

@router.post("/users", response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user_in)

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    if not crud.get_users(db):
        return 'No users in DB'
    return crud.get_users(db)
