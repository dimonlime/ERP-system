from datetime import datetime
from sqlalchemy import String, ForeignKey, Null, Text, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import json

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine, expire_on_commit=False)


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


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
