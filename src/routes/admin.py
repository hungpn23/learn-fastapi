from fastapi import APIRouter, HTTPException, Request
from sqlmodel import SQLModel, and_, or_, select

from ..constant import Role
from ..dependencies import SessionDep
from ..models import User, Set

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "admin not found"}},
)

class AddUserDto(SQLModel):
    username: str
    role: Role
    email: str
    password: str

@router.get('/all-users')
def get_all_users(session: SessionDep):
    user = session.exec(select(User)).all()

    return user

@router.post('/add-user')
def add_user(dto: AddUserDto, session: SessionDep):
    stmt = select(User).where(or_(User.username == dto.username, User.email == dto.email))
    user = session.exec(stmt).unique().one_or_none()

    if user:
        raise HTTPException(status_code=400, detail="username or email already exists")
    
    session.add(User(username=dto.username, role=dto.role, email=dto.email, password=dto.password))
    session.commit()
    return

@router.delete('/delete-user/{userId}')
def delete_user(userId: int, session: SessionDep):
    stmt = select(User).where(User.id == userId)
    user = session.exec(stmt).first()

    if not user:
        return {"error": "User not found"}

    session.delete(user)
    session.commit()

    return {"message": "User deleted successfully"}

@router.delete('/delete-set/{setId}')
def delete_set(setId: int, req: Request, session: SessionDep):

    set = session.exec(
        select(Set).where(Set.id == setId)
    ).first()

    if not set:
        raise HTTPException(status_code=404, detail="Set not found")

    for card in set.cards:
        session.delete(card)
    session.delete(set)
    session.commit()

    return