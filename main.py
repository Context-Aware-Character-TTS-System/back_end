from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
import jwt
import os
import uuid

from . import models, database, schemas, security, utils

app = FastAPI()

# Define the directory for storing uploaded novels
UPLOAD_DIRECTORY = "./uploaded_novels"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=database.engine)




@app.post("/users/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(security.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = security.hash_password(user.password)
    db_user = models.User(email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(security.get_db)):
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/logout")
def logout_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(security.get_db)):
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        jti = payload.get("jti")
        if jti is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token: JTI missing")

        revoked_token = models.RevokedToken(jti=jti)
        db.add(revoked_token)
        db.commit()
        return {"message": "Successfully logged out"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: schemas.UserResponse = Depends(security.get_current_user)):
    return current_user

@app.get("/")
def read_root():
    return {"message": "Context-Aware Character TTS System API"}

@app.post("/novels/upload", response_model=schemas.NovelResponse)
def upload_novel(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(security.get_db)
):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .txt files are allowed")

    # Generate a unique filename and path
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    # Save the uploaded file
    await utils.save_upload_file(file, file_path)

    # Create a new novel entry in the database
    db_novel = models.Novel(
        title=title,
        master_context=description, # Using master_context to store description for now
        user_id=current_user.id,
        status="pending",
        full_audio_url=file_path # Store the local file path for now
    )
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)

    return db_novel

