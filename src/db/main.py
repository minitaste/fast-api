from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.models import Book

engine = AsyncEngine(
    create_engine(
        url=Config.DATABASE_URL,
        echo=False,
    )
)


async def init_db() -> None:
    async with engine.begin() as conn:

        # Check if any model created
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with Session() as session:
        yield session
