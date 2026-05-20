"""
Seed demo user accounts.
Run once after migrations: python seed.py
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.auth import hash_password

DEMO_USERS = [
    {"email": "user1@codesentinel.dev", "password": "password123"},
    {"email": "user2@codesentinel.dev", "password": "password123"},
]


async def seed():
    async with AsyncSessionLocal() as db:
        for u in DEMO_USERS:
            existing = await db.execute(select(User).where(User.email == u["email"]))
            if existing.scalar_one_or_none():
                print(f"  already exists: {u['email']}")
                continue
            db.add(User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
            ))
            print(f"  created: {u['email']}")
        await db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
