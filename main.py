from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from fastui.components.display import DisplayLookup, DisplayMode
from starlette.responses import HTMLResponse

from database import async_main, delete_tables
from routers.router import order_router, shipment_router, cheque_router, fish_router
from typing import Annotated

from fastapi import APIRouter, Depends

from repository import OrderRepository, ShipmentRepository, ChequeRepository, FishRepository
from schemas.schemas import (SOrderAdd, SOrder, SOrderId, SShipment, SShipmentAdd, SShipmentId, SChequeAdd, SCheque,
                             SChequeId,
                             SFish, SFishAdd, SFishId)

from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.events import GoToEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await delete_tables()
    # print('База очищена')
    await async_main()
    print('База готова к работе')
    yield
    print('Выключение')


app = FastAPI(lifespan=lifespan)
app.include_router(order_router)
app.include_router(shipment_router)
app.include_router(cheque_router)
app.include_router(fish_router)


def main_page(*components: AnyComponent, title: str | None = None) -> list[AnyComponent]:
    return [
        c.PageTitle(text='GND'),
        c.Navbar(
            title='GND Control System',
            title_event=GoToEvent(url='/'),
            start_links=[
                c.Link(
                    components=[c.Text(text='Заказы')],
                    on_click=GoToEvent(url='/orders/current'),
                    active='startswith:/orders',
                ),
                c.Link(
                    components=[c.Text(text='Поставки')],
                    on_click=GoToEvent(url='/incomes'),
                    active='startswith:/incomes',
                ),
                c.Link(
                    components=[c.Text(text='Чеки')],
                    on_click=GoToEvent(url='/cheques'),
                    active='startswith:/cheques',
                ),
                c.Link(
                    components=[c.Text(text='Информация по артикулам')],
                    on_click=GoToEvent(url='/article_info'),
                    active='startswith:/article_info',
                ),
            ],
        ),
        c.Page(
            components=[
                *((c.Heading(text=title),) if title else ()),
                *components,
            ],
        ),
    ]


def tabs() -> list[AnyComponent]:
    return [
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Текущие')],
                    on_click=GoToEvent(url='/orders/current'),
                    active='startswith:/orders/current',
                ),
                c.Link(
                    components=[c.Text(text='Архив')],
                    on_click=GoToEvent(url='/orders/archive'),
                    active='startswith:/orders/archive',
                ),
            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
    ]


orders = [
    SOrder(id=1, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=512, quantity_m=412, quantity_l=322,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=2, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=122, quantity_m=212, quantity_l=722,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=3, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=12, quantity_m=612, quantity_l=252,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=4, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=12, quantity_m=612, quantity_l=252,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=5, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=12, quantity_m=612, quantity_l=252,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=6, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=12, quantity_m=612, quantity_l=252,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=7, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=12, quantity_m=612, quantity_l=252,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=8, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=12, quantity_m=612, quantity_l=252,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
    SOrder(id=9, create_date='05.07.2024', change_date='05.07.2024', internal_article='51920231',
           vendor_internal_article='Не заполнено', quantity_s=12, quantity_m=612, quantity_l=252,
           color='Черный', shop_name='KTN', sending_method='Avia', order_image='-', status='Заказ не готов',
           flag=False),
]


@app.get('/api/orders/current', response_model=FastUI, response_model_exclude_none=True)
def orders_view() -> list[AnyComponent]:
    return main_page(
        *tabs(),
        c.Table(
            data=orders,
            columns=[
                DisplayLookup(field='id', on_click=GoToEvent(url='')),
                DisplayLookup(field='create_date', mode=DisplayMode.date),
                DisplayLookup(field='change_date'),
                DisplayLookup(field='internal_article', mode=DisplayMode.markdown),
                DisplayLookup(field='vendor_internal_article', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_s', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_m', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_l', mode=DisplayMode.markdown),
                DisplayLookup(field='color', mode=DisplayMode.markdown),
                DisplayLookup(field='shop_name', mode=DisplayMode.markdown),
                DisplayLookup(field='sending_method', mode=DisplayMode.markdown),
                DisplayLookup(field='status'),
            ],
        ),
        title='Текущие заказы',
    )


@app.get('/api/orders/archive', response_model=FastUI, response_model_exclude_none=True)
def orders_view() -> list[AnyComponent]:
    return main_page(
        *tabs(),
        c.Div(
            components=[
                c.Heading(text='Модуль в разработке...', level=2),
            ],
            class_name='card-container',
        ),
        title='Архивные заказы',
    )


@app.get('/api/incomes', response_model=FastUI, response_model_exclude_none=True)
def incomes_view() -> list[AnyComponent]:
    return main_page(
        c.Div(
            components=[
                c.Heading(text='Модуль в разработке...', level=2),
            ],
            class_name='card-container',
        ),
        title='Поставки',
    )


@app.get('/api/cheques', response_model=FastUI, response_model_exclude_none=True)
def cheques_view() -> list[AnyComponent]:
    return main_page(
        c.Div(
            components=[
                c.Heading(text='Модуль в разработке...', level=2),
            ],
            class_name='card-container',
        ),
        title='Чеки',
    )


@app.get('/api/article_info', response_model=FastUI, response_model_exclude_none=True)
def articles_view() -> list[AnyComponent]:
    return main_page(
        c.Div(
            components=[
                c.Heading(text='Модуль в разработке...', level=2),
            ],
            class_name='card-container',
        ),
        title='Артикулы',
    )


@app.get('/api/', response_model=FastUI, response_model_exclude_none=True)
def components_view() -> list[AnyComponent]:
    return main_page(
        c.Div(
            components=[
                c.Heading(text='Список последних заказов', level=2),
                c.Text(text='В разработке...'),
            ],
            class_name='card-container',
        ),
        c.Div(
            components=[
                c.Heading(text='Список горящих чеков', level=2),
                c.Paragraph(text='В разработке...'),
            ],
            class_name='border-top mt-3 pt-1',
        ),
    )


@app.get('/api/', response_model=FastUI, response_model_exclude_none=True)
def api_index() -> list[AnyComponent]:
    markdown = ''
    return main_page(c.Markdown(text=markdown))


@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title='GND'))
