from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, database

app = FastAPI()

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=database.engine)

# Dependency to get a database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Context-Aware Character TTS System API"}

