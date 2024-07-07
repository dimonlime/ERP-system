from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import async_main, delete_tables
from router import order_router, shipment_router, cheque_router, fish_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await async_main()
    yield
    print('Выключение')


app = FastAPI(lifespan=lifespan)
app.include_router(order_router)
app.include_router(shipment_router)
app.include_router(cheque_router)
app.include_router(fish_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)