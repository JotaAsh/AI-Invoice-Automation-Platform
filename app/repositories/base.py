from typing import Generic, TypeVar, Type, List, Optional, Any
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """
    Abstract/Generic base repository providing standard CRUD operations 
    leveraging SQLAlchemy AsyncSession.
    """
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db = db_session

    async def get(self, id: UUID) -> Optional[ModelType]:
        """Retrieve a specific record by its primary UUID key."""
        result = await self.db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retrieve a paginated list of records."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: dict) -> ModelType:
        """Instantiate and persist a new record in the database."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        # Flush to populate the ID and default fields before commit
        await self.db.flush()
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Update an existing record with new attribute mappings."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def delete(self, id: UUID) -> bool:
        """Remove a record by its identifier from persistence."""
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
            return True
        return False