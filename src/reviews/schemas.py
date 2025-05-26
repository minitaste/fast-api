from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewModel(BaseModel):
    uid: UUID
    rating: int = Field(ge=1, lt=5)
    user_uid: Optional[UUID]
    book_uid: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class ReviewCreateModel(BaseModel):
    rating: int = Field(lt=5)
