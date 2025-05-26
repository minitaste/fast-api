from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.auth.dependencies import AccessTokenBearer, RoleChecker
from src.books.service import BookService
from src.db.main import get_session
from src.errors import BookNotFound

from .schemas import Book, BookCreateModel, BookDetailModel, BookUpdateModel

book_router = APIRouter()
book_service = BookService()
access_token_bearer = AccessTokenBearer()
role_checker = RoleChecker(["admin", "user"])


@book_router.get("/", response_model=list[Book])
async def get_all_books(
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer),
    _: bool = Depends(role_checker),
):
    books = await book_service.get_all_books(session)
    return books


@book_router.get(
    "/user/{user_uid}",
    response_model=list[Book],
)
async def get_user_books(
    user_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer),
):
    books = await book_service.get_user_books(user_uid, session)
    return books


@book_router.post("/", status_code=status.HTTP_201_CREATED, response_model=Book)
async def create_book(
    book_data: BookCreateModel,
    session: AsyncSession = Depends(get_session),
    token_details=Depends(access_token_bearer),
) -> Book:
    user_uid = token_details.get("user")["user_uid"]
    new_book = await book_service.create_book(book_data, user_uid, session)
    return new_book


@book_router.get("/{book_uid}", response_model=BookDetailModel)
async def get_book(
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details=Depends(access_token_bearer),
) -> BookDetailModel:
    book = await book_service.get_book(book_uid, session)

    if book:
        return book

    raise BookNotFound()


@book_router.patch("/{book_uid}", response_model=Book)
async def update_book(
    book_uid: str,
    book_update_data: BookUpdateModel,
    session: AsyncSession = Depends(get_session),
    token_details=Depends(access_token_bearer),
) -> Book:

    updated_book = await book_service.update_book(book_uid, book_update_data, session)

    if updated_book:
        return updated_book

    raise BookNotFound()


@book_router.delete("/{book_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details=Depends(access_token_bearer),
) -> None:

    book_to_delete = await book_service.delete_book(book_uid, session)

    if book_to_delete is None:
        raise BookNotFound()

    return {}
