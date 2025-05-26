from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from src.auth.routes import auth_router
from src.books.routes import book_router
from src.db.main import init_db
from src.reviews.routes import review_router

from .errors import (
    AccessTokenRequired,
    BookNotFound,
    InsufficientPermission,
    InvalidCredentials,
    InvalidToken,
    RefreshTokenRequired,
    UserAlreadyExists,
    UserNotFound,
    create_exception_handler,
)
from .middleware import register_middleware


@asynccontextmanager
async def life_span(app: FastAPI):
    print(f"Server is start...")
    await init_db()
    yield

    print(f"Server is stopped")


version = "v1"

app = FastAPI(
    title="BIT",
    description="hello",
    version=version,
    lifespan=life_span,
)


register_middleware(app)

app.add_exception_handler(
    UserAlreadyExists,
    create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={"message": "Email already exists."},
    ),
)


app.include_router(book_router, prefix=f"/api/{version}/books")
app.include_router(auth_router, prefix=f"/api/{version}/auth")
app.include_router(review_router, prefix=f"/api/{version}/reviews")
