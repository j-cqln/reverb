"""
models.py

ORM models for database and related classes.
"""

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Base(DeclarativeBase):
    """Base"""

class Users(Base, UserMixin):
    """Users"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    bio: Mapped[str] = mapped_column(String, nullable=True)
    favorite_track: Mapped[str] = mapped_column(String, nullable=True)
    favorite_album: Mapped[str] = mapped_column(String, nullable=True)
    favorite_genre: Mapped[str] = mapped_column(String, nullable=True)
    journal_entries = relationship("JournalEntry", back_populates="user")
    reviews = relationship("Reviews", back_populates="user")
    collections = relationship("Collections", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"{self.username}: {self.bio}"

class Reviews(Base):
    """Reviews"""
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=True)
    content_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=True)
    user = relationship("Users", back_populates="reviews")

class JournalEntry(Base):
    """Journal Entry"""
    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    def to_dict(self):
        """Convert the JournalEntry object to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_id": self.content_id,
            "text": self.text,
        }
    user = relationship("Users", back_populates="journal_entries")

class Collections(Base):
    """Collections"""
    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    image: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    collection_content = relationship("CollectionsContent", back_populates="collection")
    user = relationship("Users", back_populates="collections")

class Content(Base):
    """Content"""
    __tablename__ = "content"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    spotify_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    spotify_type: Mapped[str] = mapped_column(String, nullable=True)
    content_collection = relationship("CollectionsContent", back_populates="content")

class CollectionsContent(Base):
    """Maps content to collections"""
    __tablename__ = "collections_content"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(Integer, ForeignKey("collections.id"))
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey("content.id"))
    collection = relationship("Collections", back_populates="collection_content")
    content = relationship("Content", back_populates="content_collection")

class Friendships(Base):
    """Friendships"""
    __tablename__ = "friendships"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id1: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user_id2: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String, default='pending') #pending, accepted, declined
    user1 = relationship("Users", foreign_keys=[user_id1])
    user2 = relationship("Users", foreign_keys=[user_id2])

class ContentItem:
    """Generic representation of one data content item, used e.g. in search results."""
    def __init__(self, content_id, content_type, name, image, artists=None):
        self.content_id = content_id
        self.content_type = content_type
        self.name = name
        self.image = image
        self.artists = artists

    def __repr__(self):
        return f"{self.content_type}: {self.name}"

class ReviewContent:
    """Generic representation of a review."""
    def __init__(self, img, name, artists, content_type, content_id, rating, text):
        self.img = img
        self.name = name
        self.artists = artists
        self.content_type = content_type
        self.content_id = content_id
        self.rating = rating
        self.text = text

class JournalEntryContent:
    """Generic representation of a journal entry."""
    def __init__(self, img, name, content_type, content_id, text):
        self.img = img
        self.name = name
        self.content_type = content_type
        self.content_id = content_id
        self.text = text
