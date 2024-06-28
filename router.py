from typing import Annotated

from fastapi import APIRouter, Depends

from repository import TaskRepository
from schemas import SOrderAdd, SOrder, SOrderId

router = APIRouter(
    prefix='/orders',
    tags=['Заказы'],
)


@router.post('')
async def add_order(task: Annotated[SOrderAdd, Depends()]) -> SOrderId:
    task_id = await TaskRepository.add_one(task)
    return {'ok': True, 'task_id': task_id}


@router.get('')
async def get_tasks() -> list[SOrder]:
    tasks = await TaskRepository.find_all()
    return tasks
