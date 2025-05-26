from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import get_current_user
from src.db.main import get_session
from src.db.models import User

from .schemas import ReviewCreateModel
from .service import ReviewService

user = Depends(get_current_user)
review_router = APIRouter()
review_service = ReviewService()
session = Depends(get_session)


@review_router.post("/book/{book_uid}", status_code=status.HTTP_201_CREATED)
async def create_review(
    book_uid: str,
    review_data: ReviewCreateModel,
    current_user: User = user,
    session: AsyncSession = session,
):
    new_review = await review_service.add_review(
        user_email=current_user.email,
        book_uid=book_uid,
        review_data=review_data,
        session=session,
    )

    return new_review
