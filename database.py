from datetime import datetime
from sqlalchemy import String, ForeignKey, Null, Text, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
import json

engine = create_async_engine(url='sqlite+aiosqlite:////Users/samar/PycharmProjects/Nadziratel_Bot/db.sqlite3')

engine_ODDS = create_async_engine(url='sqlite+aiosqlite:///ODDS.sqlite3')

async_session = async_sessionmaker(engine, expire_on_commit=False)

async_session_ODDS = async_sessionmaker(engine_ODDS, expire_on_commit=False, class_=AsyncSession)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    create_date: Mapped[str] = mapped_column(String(25))
    change_date: Mapped[str] = mapped_column(String(25))
    internal_article: Mapped[str] = mapped_column(String(25))
    vendor_internal_article: Mapped[str] = mapped_column(String(50), nullable=True, default='Не заполнено')
    quantity_s: Mapped[int] = mapped_column()
    quantity_m: Mapped[int] = mapped_column()
    quantity_l: Mapped[int] = mapped_column()
    color: Mapped[str] = mapped_column(String(50))
    shop_name: Mapped[str] = mapped_column(String(25))
    sending_method: Mapped[str] = mapped_column(String(25))
    order_image: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(String(25), default='Заказ не готов')
    flag: Mapped[bool] = mapped_column(default=False)


class Shipment(Base):
    __tablename__ = 'shipments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    create_date: Mapped[str] = mapped_column(String(25))
    change_date: Mapped[str] = mapped_column(String(25), nullable=True, default=None)
    quantity_s: Mapped[int] = mapped_column()
    quantity_m: Mapped[int] = mapped_column()
    quantity_l: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(25), default='Поставка отправлена')
    sending_method: Mapped[str] = mapped_column(String(25))
    sack_number: Mapped[int] = mapped_column(nullable=True, unique=True, default=None)
    fish: Mapped[int] = mapped_column(ForeignKey('fishes.id'))
    cheque: Mapped[int] = mapped_column(ForeignKey('cheques.id'))
    document_1_id: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    document_2_id: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    image_1_id: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    image_2_id: Mapped[str] = mapped_column(String(255), nullable=True, default=None)


class Cheque(Base):
    __tablename__ = 'cheques'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey('shipments.id'), nullable=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    date: Mapped[str] = mapped_column(String(25))
    create_date: Mapped[str] = mapped_column(String(25))
    shop_name: Mapped[str] = mapped_column(String(25))
    cheque_number: Mapped[int] = mapped_column()
    vendor_internal_article: Mapped[int] = mapped_column()
    price: Mapped[int] = mapped_column()
    cheque_image_id: Mapped[str] = mapped_column(String(255))
    cheque_status: Mapped[str] = mapped_column(String(25), default='По чеку имеется отсрочка')
    payment_image: Mapped[str] = mapped_column(String(255), nullable=True, default=None)


class Fish(Base):
    __tablename__ = 'fishes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey('shipments.id'), nullable=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    fish_number: Mapped[int] = mapped_column()
    fish_date: Mapped[datetime] = mapped_column(String(25))
    weight: Mapped[int] = mapped_column()
    sack_count: Mapped[int] = mapped_column()
    sending_method: Mapped[str] = mapped_column(String(25))
    fish_image_id: Mapped[str] = mapped_column(String(255))


class ProductCard(Base):
    __tablename__ = 'product_cards'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article: Mapped[str] = mapped_column()
    image_id: Mapped[str] = mapped_column()
    color: Mapped[str] = mapped_column(String(50))
    shop_name: Mapped[str] = mapped_column(String(25))
    vendor_internal_article: Mapped[str] = mapped_column(String(50), nullable=True, default='Не заполнено')

class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    code: Mapped[str] = mapped_column()
    amount: Mapped[float] = mapped_column()
    date: Mapped[str] = mapped_column()



class Income(Base):
    __tablename__ = 'incomes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    code: Mapped[str] = mapped_column()
    amount: Mapped[float] = mapped_column()
    date: Mapped[str] = mapped_column()

    def __repr__(self):
        return f"<Income(name={self.name}, code={self.code}, amount={self.amount}, date={self.date})>"
class Costs(Base):
    __tablename__ = 'costs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    value: Mapped[float] = mapped_column()

class Credits(Base):
    __tablename__ = 'credits'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    week_number: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column()
    value: Mapped[float] = mapped_column()
    date: Mapped[str] = mapped_column()

class PaymentsPurpose(Base):
    __tablename__ = 'payments_purpose'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column()

class IncomePurpose(Base):
    __tablename__ = 'income_purpose'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column()

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[Order.__table__, Shipment.__table__, Cheque.__table__, Fish.__table__, ProductCard.__table__])

    async with engine_ODDS.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=[Payment.__table__, Income.__table__, Credits.__table__])

async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def async_session_ODDS_():
    async with async_session_ODDS() as session:
        yield session