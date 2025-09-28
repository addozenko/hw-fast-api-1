import os
import datetime

from dotenv import load_dotenv

from sqlalchemy import String, DateTime, Column, Float
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import func

load_dotenv()

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

POSTGRES_DSN = (
    f"postgresql+asyncpg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/"
    f"{POSTGRES_DB}"
)

engine = create_async_engine(POSTGRES_DSN)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class AdvertisementORM(Base):
    __tablename__ = "advertisement"

    id = Column(PGUUID(as_uuid=True), primary_key=True, index=True, default=None)
    title : MappedColumn[str] = mapped_column(String)
    description : MappedColumn[str] = mapped_column(String)
    price : MappedColumn[float] = mapped_column(Float)
    author : MappedColumn[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    await engine.dispose()