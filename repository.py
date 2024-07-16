from sqlalchemy import select

from database import async_session, Order, Shipment, Cheque, Fish, Payment, async_session_ODDS, Income
from schemas.schemas import SOrderAdd, SOrder, SFishAdd, SChequeAdd, SCheque, SFish, SShipmentAdd, SShipment, SODDSincome, SODDSpayment


class OrderRepository:
    @classmethod
    async def add_order(cls, data: SOrderAdd) -> int:
        async with async_session() as session:
            order_dict = data.model_dump()
            print(order_dict)
            order = Order(**order_dict)
            session.add(order)
            await session.flush()
            await session.commit()
            return order.id

    @classmethod
    async def all_orders(cls) -> list[SOrder]:
        async with async_session() as session:
            query = select(Order)
            result = await session.execute(query)
            order_models = result.scalars().all()
            print(order_models)
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return order_models


class ShipmentRepository:
    @classmethod
    async def add_shipment(cls, data: SShipmentAdd) -> int:
        async with async_session() as session:
            shipment_dict = data.model_dump()
            shipment = Shipment(**shipment_dict)
            session.add(shipment)
            await session.flush()
            await session.commit()
            return shipment.id

    @classmethod
    async def all_shipments(cls) -> list[SShipment]:
        async with async_session() as session:
            query = select(Shipment)
            result = await session.execute(query)
            shipment_models = result.scalars().all()
            print(shipment_models)
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return shipment_models


class ChequeRepository:
    @classmethod
    async def add_cheque(cls, data: SChequeAdd) -> int:
        async with async_session() as session:
            cheque_dict = data.model_dump()
            cheque = Cheque(**cheque_dict)
            session.add(cheque)
            await session.flush()
            await session.commit()
            return cheque.id

    @classmethod
    async def all_cheques(cls) -> list[SCheque]:
        async with async_session() as session:
            query = select(Cheque)
            result = await session.execute(query)
            cheque_models = result.scalars().all()
            print(cheque_models)
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return cheque_models


class FishRepository:
    @classmethod
    async def add_fish(cls, data: SFishAdd) -> int:
        async with async_session() as session:
            fish_dict = data.model_dump()
            fish = Fish(**fish_dict)
            session.add(fish)
            await session.flush()
            await session.commit()
            return fish.id

    @classmethod
    async def all_fishes(cls) -> list[SFish]:
        async with async_session() as session:
            query = select(Fish)
            result = await session.execute(query)
            fish_models = result.scalars().all()
            print(fish_models)
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return fish_models

class ODDSRepository:

    @classmethod
    async def all_payments(cls) -> list[SODDSpayment]:
        async with async_session_ODDS() as session:
            query = select(Payment)
            result = await session.execute(query)
            payments_models = result.scalars().all()
            return payments_models

    @classmethod
    async def all_incomes(cls) -> list[SODDSincome]:
        async with async_session_ODDS() as session:
            query = select(Income)
            result = await session.execute(query)
            incomes_models = result.scalars().all()
            return incomes_models
