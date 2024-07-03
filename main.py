from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import async_main, delete_tables
from router import order_router, shipment_router, cheque_router, fish_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await delete_tables()
    print('База очищена')
    await async_main()
    print('База готова к работе')
    yield
    print('Выключение')


app = FastAPI(lifespan=lifespan)
app.include_router(order_router)
app.include_router(shipment_router)
app.include_router(cheque_router)
app.include_router(fish_router)
