import asyncio
from uuid import UUID
from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.api.books import process_book
from app.models.user import User
from sqlalchemy import select

@celery_app.task(name="tasks.process_book", bind=True, max_retries=3)
def process_book_task(self, book_id_str: str, user_id_str: str):
    """Celery background task to process and ingest a book asynchronously."""
    async def _async_run():
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == UUID(user_id_str))
            user = (await session.execute(stmt)).scalar_one_or_none()
            if not user:
                raise ValueError(f"User {user_id_str} not found")
            await process_book(book_id=UUID(book_id_str), current_user=user, db=session)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run(_async_run())
        else:
            loop.run_until_complete(_async_run())
        return {"status": "success", "book_id": book_id_str}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
