from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Category, User
from app.schemas import CategoryCreate
from app.deps import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("")
def list_categories(
    type: str | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    q = select(Category).where(Category.user_id == current_user.id)
    if type:
        q = q.where(Category.type == type)
    return session.exec(q).all()

@router.post("")
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    cat = Category(user_id=current_user.id, name=payload.name, type=payload.type)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return cat

@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    cat = session.get(Category, category_id)
    if not cat or cat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(cat)
    session.commit()
    return {"message": "deleted"}
