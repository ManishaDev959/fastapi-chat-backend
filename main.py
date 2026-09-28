# main.py
# This is the entry point of the backend - equivalent to Startup.cs / Program.cs
# in a .NET Web API project. It defines every HTTP endpoint the Angular
# frontend will call.

# from fastapi import FastAPI, Depends, HTTPException


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models
from models import User, BlacklistedToken, Conversation, Message
from schemas import UserCreate, UserOut, Token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


import schemas
from database import engine, get_db, Base
from llm_chain import get_ai_response
from datetime import datetime, timedelta


# This line looks at every class in models.py that inherits from Base
# and creates the matching SQL tables if they don't already exist.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ChatGPT Clone API")

# Browsers block cross-origin requests by default (Angular runs on port 4200,
# this API runs on port 8000 - different origins). CORS middleware explicitly
# allows the Angular app to call this API.
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:4200"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular's dev server
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # includes Authorization header for your JWT
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Runs automatically for any route that declares
    `current_user: User = Depends(get_current_user)`.
    Steps:
      1. Reject the token if it's been blacklisted (user logged out).
      2. Decode + verify the JWT signature/expiry.
      3. Look up the user it refers to.
      4. Return that User object to the route, or raise 401 if anything failed.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check the blacklist FIRST - a logged-out token should never pass,
    # even if it hasn't technically expired yet.
    if db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first():
        raise credentials_error

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    username = payload.get("sub")
    if username is None:
        raise credentials_error

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_error

    return user

   



# Registering User 

@app.post("/register", response_model=UserOut)
def register(user_in : UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exixts")

    new_user =User(
        username = user_in.username,
        hashed_password = hash_password(user_in.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
    


#login user 

@app.post("/login", response_model=Token)
def login(formdata : OAuth2PasswordRequestForm = Depends(), db : Session = Depends(get_db)):

    user = db.query(User).filter(User.username == formdata.username).first()
    if not user or not verify_password(formdata.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
    return {"access_token": access_token, "token_type": "bearer"}




@app.post("/conversations", response_model=schemas.ConversationOut)
def create_conversation(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    conversation = models.Conversation(title="New Chat", user_id=current_user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@app.get("/conversations", response_model=List[schemas.ConversationOut])
def list_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.created_at.desc()).all()


@app.get("/conversations/{conversation_id}", response_model=schemas.ConversationDetail)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"ok": True}


@app.post("/conversations/{conversation_id}/messages", response_model=schemas.MessageOut)
def send_message(conversation_id: int, message: schemas.MessageCreate,  current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
 
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

  
    user_msg = models.Message(conversation_id=conversation_id,user_id=current_user.id, role="user", content=message.content)
    db.add(user_msg)
    db.commit()

   
    if conversation.title == "New Chat":
        conversation.title = message.content[:40]
        db.commit()


    past_messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    history = [(m.role, m.content) for m in past_messages[:-1]]

    ai_text = get_ai_response(history, message.content)

    ai_msg = Message(conversation_id=conversation_id, role="assistant", content=ai_text)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return ai_msg

@app.post("/logout")
def logout_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
  
    blacklisted = BlacklistedToken(token=token)
    db.add(blacklisted)
    db.commit()
    return {"ok": True, "message": "Logged out successfully."}