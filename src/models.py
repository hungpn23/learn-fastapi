# ref: https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/

from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from database import engine
from constant import Role, VisibleTo

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: Role = Field(default=Role.USER)
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    isEmailVerified: bool = Field(default=False)
    password: str | None = Field(nullable=True)
    bio: str | None = Field(nullable=True)
    avatar: str | None = Field(nullable=True)

    sessions: list["Session"] = Relationship(back_populates="user")
    sets: list["Set"] = Relationship(back_populates="user")

class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    signature: str
    expires_at: datetime
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")

    user: User | None = Relationship(back_populates="sessions")

class Set(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str = Field(nullable=True)
    visible_to: VisibleTo = Field(default=VisibleTo.JUST_ME)
    passcode: str | None = Field(nullable=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    author_id: int = Field(foreign_key="user.id", ondelete="CASCADE")

    user: User | None = Relationship(back_populates="sets")
    author: User | None = Relationship(back_populates="sets")
    cards: list["Card"] = Relationship(back_populates="set")

class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    term: str
    definition: str
    correct_count: int = Field(nullable=True)
    set_id: int = Field(foreign_key="set.id", ondelete="CASCADE")

    set: Set | None = Relationship(back_populates="cards")

# ref: https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#refactor-data-creation
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()