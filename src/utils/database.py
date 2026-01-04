from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase
import os 
from dotenv import load_dotenv
from collections.abc import AsyncGenerator
from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase
)

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

# Defining Database url
DB_URL = os.getenv("DATABASE_URL")

# Initializing Base model 

class Base(DeclarativeBase):
    pass


engine = create_async_engine(DB_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)