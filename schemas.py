# schemas.py
# These are NOT database tables. They define what JSON shape goes IN and OUT
# of our API. FastAPI uses these to validate requests and format responses.
# Think of them as the "DTOs" you'd use in a .NET Web API controller.

from pydantic import BaseModel
from datetime import datetime
from typing import List


class UserCreate(BaseModel):
    username : str
    password : str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        # Lets Pydantic build this directly from a SQLAlchemy User object
        # instead of requiring a plain dict.
        from_attributes = True



class Token(BaseModel):        
    access_token : str
    token_type : str



class MessageCreate(BaseModel):
    """What the frontend sends us when the user sends a message."""
    content: str


class MessageOut(BaseModel):
    """What we send back to the frontend for a single message."""
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        # This lets Pydantic read data directly from SQLAlchemy model objects,
        # not just plain dicts.
        from_attributes = True


class ConversationOut(BaseModel):
    """Basic info about a conversation - used in the sidebar list."""
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    """Full conversation, including all its messages - used when you open a chat."""
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True
