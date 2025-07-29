from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    novels = relationship("Novel", back_populates="owner")

class Novel(Base):
    __tablename__ = 'novels'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    status = Column(Enum('pending', 'processing', 'done', 'error', name='novel_status'), default='pending')
    full_audio_url = Column(Text, nullable=True)
    master_context = Column(Text, nullable=True) # JSON stored as string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="novels")
    sentences = relationship("Sentence", back_populates="novel")

class Sentence(Base):
    __tablename__ = 'sentences'
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey('novels.id'))
    sentence_index = Column(Integer)
    text = Column(Text)
    speaker = Column(String)
    emotion = Column(String)
    instruction = Column(Text)
    voice_id = Column(String)
    audio_url = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    novel = relationship("Novel", back_populates="sentences")