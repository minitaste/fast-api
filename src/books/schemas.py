from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.reviews.schemas import ReviewModel


class Book(BaseModel):
    uid: UUID
    title: str
    description: str
    author: str
    created_at: datetime
    updated_at: datetime


class BookDetailModel(Book):
    reviews: list[ReviewModel]


class BookCreateModel(BaseModel):
    title: str
    description: str
    author: str


class BookUpdateModel(BaseModel):
    title: str
    description: str
