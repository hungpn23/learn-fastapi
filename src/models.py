# ref: https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/

import random
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine

from .constant import Role, VisibleTo

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: Role = Field(default=Role.USER)
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    isEmailVerified: bool = Field(default=False)
    password: str | None = Field(nullable=True)
    bio: str | None = Field(nullable=True)
    avatar: str | None = Field(nullable=True)

    setsOwned: list["Set"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "Set.userId"}
    )
    setsCreated: list["Set"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"foreign_keys": "Set.authorId"}
    )

class Set(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str = Field(nullable=True)
    visibleTo: VisibleTo = Field(default=VisibleTo.JUST_ME)
    passcode: str | None = Field(nullable=True)
    userId: int = Field(foreign_key="user.id")
    authorId: int = Field(foreign_key="user.id")

    user: User | None = Relationship(
        back_populates="setsOwned",
        sa_relationship_kwargs={"foreign_keys": "Set.userId"}
    )
    author: User | None = Relationship(
        back_populates="setsCreated",
        sa_relationship_kwargs={"foreign_keys": "Set.authorId"}
    )
    cards: list["Card"] = Relationship(back_populates="set")

class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    term: str
    definition: str
    correctCount: int = Field(nullable=True)
    createdBy: int
    setId: int = Field(foreign_key="set.id")

    set: Set | None = Relationship(back_populates="cards")

# ref: https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#engine-echo
engine = create_engine("postgresql+psycopg2://user:password@127.0.0.1:5432/database", echo=True)

# ref: https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#refactor-data-creation
def create_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

def get_random_cards(userId: int):
    rare_words = [
        {"term": "aberration", "definition": "sự lệch lạc, lệch chuẩn"},
        {"term": "acquiesce", "definition": "chịu đựng, đồng thuận mặc dù không hứng thú"},
        {"term": "alacrity", "definition": "sự nhanh nhẹn, sẵn lòng"},
        {"term": "anomaly", "definition": "điều bất thường"},
        {"term": "antithesis", "definition": "điều đối lập, nghịch lý"},
        {"term": "arcane", "definition": "bí ẩn, huyền bí"},
        {"term": "ascetic", "definition": "khổ hạnh, giản dị"},
        {"term": "cacophony", "definition": "âm thanh hỗn loạn"},
        {"term": "capitulate", "definition": "đầu hàng, chịu thua"},
        {"term": "catharsis", "definition": "sự giải tỏa cảm xúc"},
    ]
    count = random.randint(10, 30)
    shuffled = random.sample(rare_words, len(rare_words))
    selected = shuffled[:count]
    return [Card(term=word["term"], definition=word["definition"], correctCount=None, createdBy=userId) for word in selected]

def seed_data(session: Session):
    users = [
        User(
            username="hungpn23",
            email="hungpn23@gmail.com",
            password="password",
            role=Role.ADMIN,
        ),
        User(
            username="andy_dufresne",
            email="andy@gmail.com",
            bio="Chuyên gia thiết kế giao diện và phát triển frontend.",
            password="password",
        ),
        User(
            username="forrest_gump",
            email="forrest@gmail.com",
            bio="Nhà phát triển full-stack với đam mê công nghệ mới.",
            password="password",
        ),
        User(
            username="cooper",
            email="cooper@gmail.com",
            bio="Kỹ sư phần mềm với kinh nghiệm đa dạng về hệ thống.",
            password="password",
        ),
        User(
            username="murphy",
            email="murphy@gmail.com",
            bio="Kiến trúc sư hệ thống, yêu thích học hỏi và đổi mới.",
            password="password",
        ),
    ]
    session.add_all(users)
    session.commit()

    sets = [
        Set(
            name="Từ vựng IELTS Reading 19 - Test 3: Passage 2",
            description="Tập hợp từ vựng về môi trường và sinh thái",
            visibleTo=VisibleTo.EVERYONE,
            passcode=None,
            userId=users[0].id,
            authorId=users[0].id,
            cards=get_random_cards(users[0].id),
        ),
        Set(
            name="Từ vựng IELTS Reading 20 - Test 4: Passage 1",
            description="Các từ vựng chuyên ngành trong bài đọc IELTS",
            visibleTo=VisibleTo.PEOPLE_WITH_A_PASSCODE,
            passcode="passcode",
            userId=users[0].id,
            authorId=users[0].id,
            cards=get_random_cards(users[0].id),
        ),
        Set(
            name="Từ vựng IELTS Reading 21 - Test 2: Passage 3",
            description="Tập hợp từ vựng nâng cao cho luyện thi IELTS",
            visibleTo=VisibleTo.JUST_ME,
            passcode=None,
            userId=users[0].id,
            authorId=users[0].id,
            cards=get_random_cards(users[0].id),
        ),
        Set(
            name="Từ vựng IELTS Reading Cambridge 18 - Test 3",
            description="Danh sách từ vựng cơ bản cho IELTS Reading",
            visibleTo=VisibleTo.EVERYONE,
            passcode=None,
            userId=users[1].id,
            authorId=users[1].id,
            cards=get_random_cards(users[1].id),
        ),
        Set(
            name="Từ vựng IELTS Reading Cambridge 19 - Test 1",
            description="Các từ vựng khó trong phần đọc IELTS",
            visibleTo=VisibleTo.JUST_ME,
            passcode=None,
            userId=users[1].id,
            authorId=users[1].id,
            cards=get_random_cards(users[1].id),
        ),
        Set(
            name="Từ vựng IELTS Reading 22 - Test 2: Passage 1",
            description="Tập hợp các thuật ngữ trong đọc hiểu IELTS",
            visibleTo=VisibleTo.EVERYONE,
            passcode=None,
            userId=users[2].id,
            authorId=users[2].id,
            cards=get_random_cards(users[2].id),
        ),
        Set(
            name="Từ vựng IELTS Reading 23 - Test 5: Passage 4",
            description="Bộ từ vựng chuyên sâu dành cho kỳ thi IELTS",
            visibleTo=VisibleTo.PEOPLE_WITH_A_PASSCODE,
            passcode="passcode",
            userId=users[2].id,
            authorId=users[2].id,
            cards=get_random_cards(users[2].id),
        ),
        Set(
            name="Từ vựng IELTS Reading 24 - Test 3: Passage 3",
            description="Các từ vựng thường gặp trong phần đọc IELTS",
            visibleTo=VisibleTo.EVERYONE,
            passcode=None,
            userId=users[3].id,
            authorId=users[3].id,
            cards=get_random_cards(users[3].id),
        ),
        Set(
            name="Từ vựng IELTS Reading Cambridge 20 - Test 2",
            description="Danh sách từ vựng thiết yếu cho IELTS Reading",
            visibleTo=VisibleTo.EVERYONE,
            passcode=None,
            userId=users[4].id,
            authorId=users[4].id,
            cards=get_random_cards(users[4].id),
        ),
    ]
    session.add_all(sets)
    session.commit()

    print(">>>>>>>> Seeding completed!")

if __name__ == "__main__":
    with Session(engine) as session:
        create_db_and_tables()
        seed_data(session)