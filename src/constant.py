from enum import Enum

class Role(str, Enum):  
    ADMIN = "admin"
    USER = "user"

class VisibleTo(str, Enum):
    EVERYONE = "everyone"
    JUST_ME = "just me"
    PEOPLE_WITH_A_PASSCODE = "people with a passcode"

PUBLIC_ROUTES = {"/auth/login", "/auth/register"}

JWT_SECRET = 'secret'