from sqlalchemy import select

from database import async_session, Order
from schemas import SOrderAdd, SOrder, SOrderId


class TaskRepository:
    @classmethod
    async def add_one(cls, data: SOrderAdd) -> int:
        async with async_session() as session:
            task_dict = data.model_dump()
            task = Order(**task_dict)
            session.add(task)
            await session.flush()
            await session.commit()
            return task.id

    @classmethod
    async def find_all(cls) -> list[SOrder]:
        async with async_session() as session:
            query = select(Order)
            result = await session.execute(query)
            task_models = result.scalars().all()
            print(task_models)
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return task_models
