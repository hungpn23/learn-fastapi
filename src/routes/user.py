from fastapi import APIRouter, Request
from sqlmodel import SQLModel, select

from ..dependencies import SessionDep
from ..models import User

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "user not found"}},
)

class UpdateUserDto(SQLModel):
    username: str | None = None
    email: str | None = None
    bio: str | None = None

@router.get('')
def get_profile(req: Request, session: SessionDep):
    stmt = select(User).where(User.id == req.state.userId)
    user = session.exec(stmt).first()

    return user

@router.patch('')
def update_profile(req: Request, dto: UpdateUserDto, session: SessionDep):
    stmt = select(User).where(User.id == req.state.userId)
    user = session.exec(stmt).first()

    if not user:
        return {"error": "User not found"}

    user.username = dto.username or user.username
    user.email = dto.email or user.email
    user.bio = dto.bio or user.bio

    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@router.delete('')
def delete_profile(req: Request, session: SessionDep):
    stmt = select(User).where(User.id == req.state.userId)
    user = session.exec(stmt).first()

    if not user:
        return {"error": "User not found"}

    session.delete(user)
    session.commit()

    return {"message": "User deleted successfully"}
