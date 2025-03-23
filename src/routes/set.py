from fastapi import APIRouter, HTTPException, Request
from sqlmodel import SQLModel, and_, join, not_, select, or_

from ..dependencies import SessionDep
from ..models import Card, Set
from ..constant import JWT_SECRET, VisibleTo

router = APIRouter(
    prefix="/set",
    tags=["set"],
    responses={404: {"description": "set not found"}},
)

@router.get("/library")
def find_all(req: Request, session: SessionDep):
    stmt = select(Set).where(Set.userId == req.state.userId)
    sets = session.exec(stmt).all()

    return format_sets(sets)

@router.get("/library/{setId}")
def find_one(setId: int, req: Request, session: SessionDep):
    stmt = select(Set).where(and_(Set.id == setId, Set.userId == req.state.userId))
    set = session.exec(stmt).first()
    
    return {**set.model_dump(), "cards": set.cards, "author": set.author}

@router.get("/explore")
def find_all_public(req: Request, session: SessionDep):
    stmt = select(Set).where(and_(not_(Set.userId == req.state.userId), or_(Set.visibleTo == VisibleTo.EVERYONE, Set.visibleTo == VisibleTo.PEOPLE_WITH_A_PASSCODE)))
    sets = session.exec(stmt).all()

    result = []
    for set in sets:
        result.append({**set.model_dump(), "author": set.author, "cards": set.cards})

    return result

@router.get("/explore/{setId}")
def find_all_public(setId: int, req: Request, session: SessionDep):
    stmt = select(Set).where(and_(Set.id == setId, not_(Set.userId == req.state.userId), or_(Set.visibleTo == VisibleTo.EVERYONE, Set.visibleTo == VisibleTo.PEOPLE_WITH_A_PASSCODE)))
    set = session.exec(stmt).first()

    return {**set.model_dump(), "cards": set.cards, "author": set.author}

def format_sets(sets: list[Set]):
    formatted = []
    for set in sets:
        set_detail = {
            "set": set, 
            "metadata": get_set_metadata(set.cards),
        }
        formatted.append(set_detail)

    return formatted

def get_set_metadata(cards: list[Card]):
    metadata = {
        "totalCards": len(cards),
        "notStudiedCount": 0,
        "learningCount": 0,
        "knownCount": 0,
    }

    for card in cards:
        if card.correctCount is None:
            metadata["notStudiedCount"] += 1
        elif card.correctCount >= 2:
            metadata["knownCount"] += 1
        else:
            metadata["learningCount"] += 1
    
    return metadata