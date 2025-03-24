from fastapi import APIRouter, HTTPException, Request
from sqlmodel import SQLModel, and_, join, not_, select, or_

from ..dependencies import SessionDep
from ..models import Card, Set, User
from ..constant import JWT_SECRET, VisibleTo

router = APIRouter(
    prefix="/set",
    tags=["set"],
    responses={404: {"description": "set not found"}},
)

class SaveAnswerDto(SQLModel):
    isCorrect: bool

class StartLearningDto(SQLModel):
    passcode: str | None = None

class CreateSetDto(SQLModel):
    name: str
    description: str | None = None
    visibleTo: VisibleTo
    passcode: str | None = None
    cards: list["CardDto"]

class UpdateSetDto(SQLModel):
    name: str | None = None
    description: str | None = None
    visibleTo: VisibleTo | None = None
    passcode: str | None = None
    cards: list["CardDto"] | None = None

class CardDto(SQLModel):
    id: int | None = None
    term: str
    definition: str

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
def find_one_public(setId: int, req: Request, session: SessionDep):
    stmt = select(Set).where(and_(Set.id == setId, not_(Set.userId == req.state.userId), or_(Set.visibleTo == VisibleTo.EVERYONE, Set.visibleTo == VisibleTo.PEOPLE_WITH_A_PASSCODE)))
    set = session.exec(stmt).first()

    return {**set.model_dump(), "cards": set.cards, "author": set.author}

@router.get("/flashcard/{setId}")
def find_one_and_metadata(setId: int, req: Request, session: SessionDep):
    stmt = select(Set).where(and_(Set.id == setId, Set.userId == req.state.userId))
    set = session.exec(stmt).first()

    set_detail = {**set.model_dump(), "cards": set.cards, "author": set.author}

    return {"set": set_detail, "metadata": get_set_metadata(set.cards)}

@router.post("/flashcard/save-answer/{cardId}")
def save_answer(cardId: int, req: Request, dto: SaveAnswerDto, session: SessionDep):
    stmt = select(Card).where(and_(Card.id == cardId, Card.createdBy == req.state.userId))
    card = session.exec(stmt).first()

    if card is None:
        raise HTTPException(status_code=404)

    card.correctCount = card.correctCount if card.correctCount is not None else 0

    if dto.isCorrect:
        card.correctCount += 1
    else:
        card.correctCount = max(0, card.correctCount - 1)

    session.add(card)
    session.commit()
    session.refresh(card)

    return {**card.model_dump(), "set": card.set}

@router.post("/flashcard/reset/{setId}")
def resetFlashcard(setId: int, req: Request, session: SessionDep):
    stmt = select(Card).where(and_(Card.setId == setId, Card.createdBy == req.state.userId))
    cards = session.exec(stmt).all()

    for card in cards:
        card.correctCount = None

    session.add_all(cards)
    session.commit()

    return

@router.post("/start-learning/{setId}")
def start_learning(setId: int, req: Request, dto: StartLearningDto, session: SessionDep):
    userId = req.state.userId

    user = session.exec(select(User).where(User.id == userId)).first()
    set = session.exec(select(Set).where(Set.id == setId)).first()

    if not user or not set:
        raise HTTPException(status_code=404)

    if set.visibleTo == VisibleTo.PEOPLE_WITH_A_PASSCODE:
        if dto.passcode != set.passcode:
            raise HTTPException(status_code=400, detail="Invalid passcode!!!")

    newCards = [
        Card(term=card.term, definition=card.definition, createdBy=userId) for card in set.cards
    ]

    newSet = Set(
        name=set.name,
        description=set.description,
        author=set.author,
        visibleTo=VisibleTo.JUST_ME,
        cards=newCards,
        user=user,
    )

    session.add(newSet)
    session.commit()
    session.refresh(newSet)

    return {**newSet.model_dump(), "cards": newSet.cards}

@router.post("/create-set")
def create_set(req: Request, dto: CreateSetDto, session: SessionDep):
    userId = req.state.userId

    found = session.exec(
        select(Set).where(and_(Set.name == dto.name, Set.userId == userId))
    ).first()

    if found:
        raise HTTPException(status_code=409, detail="Set with this name already exists")

    if len(dto.cards) < 4:
        raise HTTPException(status_code=400, detail="Minimum 4 cards required")

    user = session.exec(select(User).where(User.id == userId)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    passcode = None
    if dto.visibleTo == VisibleTo.PEOPLE_WITH_A_PASSCODE:
        passcode = dto.passcode

    cards = [Card(term=card.term, definition=card.definition, createdBy=userId) for card in dto.cards]

    newSet = Set(
        name=dto.name,
        description=dto.description,
        visibleTo=dto.visibleTo,
        passcode=passcode,
        userId=userId,
        authorId=userId,
        cards=cards,
        user=user,
        author=user,
    )

    session.add(newSet)
    session.commit()
    session.refresh(newSet)

    return newSet.model_dump()

@router.patch("/edit-set/{setId}")
def update_set(setId: int, req: Request, dto: UpdateSetDto, session: SessionDep):
    userId = req.state.userId

    set = session.exec(
        select(Set).where(and_(Set.id == setId, Set.userId == userId))
    ).first()

    if not set:
        raise HTTPException(status_code=404, detail="Set not found")

    if dto.name is not None:
        set.name = dto.name
    if dto.description is not None:
        set.description = dto.description
    if dto.visibleTo is not None:
        set.visibleTo = dto.visibleTo

    if dto.visibleTo == VisibleTo.EVERYONE or dto.visibleTo == VisibleTo.JUST_ME:
        set.passcode = None
    elif dto.visibleTo == VisibleTo.PEOPLE_WITH_A_PASSCODE:
        set.passcode = dto.passcode

    if dto.cards is not None:
        cardMap = {card.id: card for card in set.cards if card.id is not None}

        newCards = []
        for cardDto in dto.cards:
            if cardDto.id and cardDto.id in cardMap:
                card = cardMap[cardDto.id]
                if card.term != cardDto.term or card.definition != cardDto.definition:
                    card.term = cardDto.term
                    card.definition = cardDto.definition
                    card.correctCount = None
                newCards.append(card)
            else:
                newCard = Card(term=cardDto.term, definition=cardDto.definition, createdBy=userId, set=set, setId=set.id)
                newCards.append(newCard)

        currentCardIds = {card.id for card in newCards if card.id is not None}
        for card in set.cards:
            if card.id not in currentCardIds:
                session.delete(card)

        set.cards = newCards

    session.add(set)
    session.commit()
    session.refresh(set)

    return {**set.model_dump(), "cards": set.cards}

@router.delete("/delete-set/{setId}")
def delete_set(setId: int, req: Request, session: SessionDep):
    userId = req.state.userId

    set = session.exec(
        select(Set).where(and_(Set.id == setId, Set.userId == userId))
    ).first()

    if not set:
        raise HTTPException(status_code=404, detail="Set not found")

    for card in set.cards:
        session.delete(card)
    session.delete(set)
    session.commit()

    return

# utils
def format_sets(sets: list[Set]):
    formatted = []
    for set in sets:
        set_detail = {
            "set": {**set.model_dump(), "cards": set.cards, "author": set.author}, 
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