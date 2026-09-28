# models.py
# These classes define the shape of our database tables.
# SQLAlchemy turns each class into a real SQL table.

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)



class BlacklistedToken(Base):
    """
    JWTs are "stateless" by design - the server doesn't normally track
    which tokens are still valid, it just checks the signature and
    expiry date. That means a real "logout" (invalidate THIS token right
    now) needs extra bookkeeping. This table is that bookkeeping: when a
    user logs out, we record their token here, and reject any future
    request that tries to use it again - even though it hasn't expired yet.
    """
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)     


class Conversation(Base):
  
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

    # This creates a Python-side link: conversation.messages gives you
    # all Message rows that belong to this conversation.
    # cascade="all, delete-orphan" means: delete a conversation -> its messages go too.
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
   
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)       # "user" or "assistant"
    content = Column(Text)      # the actual message text
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
