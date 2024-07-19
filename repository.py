from datetime import datetime
from typing import List

from sqlalchemy import select

from database import async_session, Order, Shipment, Cheque, Fish, Payment, async_session_ODDS, Income
from schemas.schemas import SOrderAdd, SOrder, SFishAdd, SChequeAdd, SCheque, SFish, SShipmentAdd, SShipment, SODDSincome, SODDSpayment
from database import async_session, Order, Shipment, Cheque, Fish, ProductCard, Payment, async_session_ODDS, Income
from schemas.schemas import SOrderAdd, SOrder, SFishAdd, SChequeAdd, SCheque, SFish, SShipmentAdd, SShipment, \
    SOrderAddForm, SODDSincome, SODDSpayment


class OrderRepository:
    @classmethod
    async def add_order(cls, data: SOrderAddForm) -> int:
        async with async_session() as session:
            order_dict = data.model_dump()
            article = order_dict.get('internal_article').value
            card = await ProductCardRepository.get_product_card(str(article))
            order = Order(**order_dict)
            order.create_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            order.change_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            order.order_image = card.image_id
            order.flag = False
            order.color = card.color
            order.shop_name = card.shop_name
            order.vendor_internal_article = card.vendor_internal_article
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
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return order_models

    @classmethod
    async def get_order(cls, order_id) -> SOrder:
        async with async_session() as session:
            query = select(Order).where(Order.id == order_id)
            result = await session.execute(query)
            order_model = result.scalar()
            # task_schemas = [SOrder.model_validate(task_model) for task_model in order_model]
            return order_model


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
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return shipment_models

    @classmethod
    async def get_shipment(cls, shipment_id) -> SShipment:
        async with async_session() as session:
            query = select(Shipment).where(Shipment.id == shipment_id)
            result = await session.execute(query)
            shipment_model = result.scalar()
            # task_schemas = [SOrder.model_validate(task_model) for task_model in order_model]
            return shipment_model


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
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return cheque_models

    @classmethod
    async def get_cheque(cls, cheque_id) -> SCheque:
        async with async_session() as session:
            query = select(Cheque).where(Cheque.id == cheque_id)
            result = await session.execute(query)
            cheque_model = result.scalar()
            # task_schemas = [SOrder.model_validate(task_model) for task_model in order_model]
            return cheque_model


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
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return fish_models

    @classmethod
    async def get_fish(cls, fish_id) -> SFish:
        async with async_session() as session:
            query = select(Fish).where(Fish.id == fish_id)
            result = await session.execute(query)
            fish_model = result.scalar()
            # task_schemas = [SOrder.model_validate(task_model) for task_model in order_model]
            return fish_model


class ProductCardRepository:
    @classmethod
    async def all_cards(cls):
        async with async_session() as session:
            query = select(ProductCard)
            result = await session.execute(query)
            product_card_models = result.scalars().all()
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return product_card_models

    @classmethod
    async def get_product_card(cls, article):
        async with async_session() as session:
            query = select(ProductCard).where(ProductCard.article == article)
            result = await session.execute(query)
            product_card_model = result.scalar()
            # task_schemas = [SOrder.model_validate(task_model) for task_model in task_models]
            return product_card_model

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
