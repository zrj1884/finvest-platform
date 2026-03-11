"""User CRUD operations."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_oauth(db: AsyncSession, provider: str, oauth_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, **kwargs: Any) -> User:
    user = User(**kwargs)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User, **kwargs: Any) -> User:
    for key, value in kwargs.items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user
