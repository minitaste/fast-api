from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.books.schemas import Book
from src.reviews.schemas import ReviewModel


class EmailModel(BaseModel):
    adressess: list[str]


class UserCreateModel(BaseModel):
    username: str = Field(max_length=50)
    first_name: str
    last_name: str
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=64)


class UserModel(BaseModel):
    uid: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    password_hash: str = Field(exclude=True)
    created_at: datetime
    updated_at: datetime


class UserLoginModel(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=64)


class UserBooksModel(UserModel):
    books: list[Book]
    reviews: list[ReviewModel]


class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str
