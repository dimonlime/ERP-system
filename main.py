from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import async_main, delete_tables
from router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await delete_tables()
    print('База очищена')
    await async_main()
    print('База готова к работе')
    yield
    print('Выключение')


app = FastAPI(lifespan=lifespan)
app.include_router(router)





