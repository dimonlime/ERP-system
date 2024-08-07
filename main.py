import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import aiofiles
import fastapi
import fastui
import pydantic
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import base64

from fastui.components.display import DisplayLookup, DisplayMode
from fastui.forms import fastui_form
from starlette.responses import HTMLResponse

from database import async_main, delete_tables, async_session, LogistWarehouse, FullfilmenttWarehouse, \
    WildberriesWarehouse, OzonWarehouse, YandexWarehouse, MovementHistory
from routers.router import order_router, shipment_router, cheque_router, fish_router, router
from typing import Annotated

from fastapi import APIRouter, Depends

from repository import (OrderRepository, ShipmentRepository, ChequeRepository, FishRepository, ProductCardRepository,
                        LogistWarehouseRepository, FullfilmentWarehouseRepository, WildberriesWarehouseRepository,
                        OzonWarehouseRepository,
                        YandexWarehouseRepository, HistoryWarehouseRepository)
from schemas.schemas import (SOrderAdd, SOrder, SOrderId, SShipment, SShipmentAdd, SShipmentId, SChequeAdd, SCheque,
                             SChequeId,
                             SFish, SFishAdd, SFishId, SOrderAddForm, SWarehouse, SWarehouseMovementForm,
                             SWarehouseMovementHistory, SWarehouseMovementAddFileForm)

from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.events import GoToEvent, BackEvent, PageEvent
from sqlalchemy import select
from fastapi import params as fastapi_params
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import HTTPException


from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.discovery import build
import pprint
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await delete_tables()
    # print('База очищена')
    #await async_main()
    # print('База готова к работе')
    yield
    print('Выключение')


app = FastAPI(lifespan=lifespan)
app.include_router(order_router)
# app.include_router(shipment_router)
app.include_router(cheque_router)
app.include_router(fish_router)
app.include_router(router)


def patched_fastui_form(model: type[fastui.forms.FormModel]) -> fastapi_params.Depends:
    async def run_fastui_form(request: fastapi.Request):
        async with request.form() as form_data:
            model_data = fastui.forms.unflatten(form_data)

            try:
                yield model.model_validate(model_data)
            except pydantic.ValidationError as e:
                raise fastapi.HTTPException(
                    status_code=422,
                    detail={'form': e.errors(include_input=False, include_url=False, include_context=False)},
                )

    return fastapi.Depends(run_fastui_form)


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
                    on_click=GoToEvent(url='/shipments/current'),
                    active='startswith:/shipments',
                ),
                c.Link(
                    components=[c.Text(text='Чеки')],
                    on_click=GoToEvent(url='/cheques/fire'),
                    active='startswith:/cheques',
                ),
                c.Link(
                    components=[c.Text(text='Склады')],
                    on_click=GoToEvent(url='/warehouse/logist'),
                    active='startswith:/warehouse/logist',
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


def order_tabs() -> list[AnyComponent]:
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
                c.Link(
                    components=[c.Text(text='Добавить заказ')],
                    on_click=GoToEvent(url='/orders/add_order'),
                    active='startswith:/orders/add_order',
                ),
            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
    ]


def shipment_tabs() -> list[AnyComponent]:
    return [
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Поставки')],
                    on_click=GoToEvent(url='/shipments/current'),
                    active='startswith:/shipments/current',
                ),
            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
    ]


def cheque_tabs() -> list[AnyComponent]:
    return [
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Горящие чеки')],
                    on_click=GoToEvent(url='/cheques/fire'),
                    active='startswith:/cheques/fire',
                ),
                c.Link(
                    components=[c.Text(text='Чеки с отстрочкой')],
                    on_click=GoToEvent(url='/cheques/delay'),
                    active='startswith:/cheques/delay',
                ),
                c.Link(
                    components=[c.Text(text='Архив')],
                    on_click=GoToEvent(url='/cheques/archive'),
                    active='startswith:/cheques/archive',
                ),
            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
    ]


def warehouse_tabs() -> list[AnyComponent]:
    return [
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Склад логистов')],
                    on_click=GoToEvent(url='/warehouse/logist'),
                    active='startswith:/warehouse/logist',
                ),
                c.Link(
                    components=[c.Text(text='Склад фуллфилмент')],
                    on_click=GoToEvent(url='/warehouse/fullfilment'),
                    active='startswith:/warehouse/fullfilment',
                ),
                c.Link(
                    components=[c.Text(text='Склад wb')],
                    on_click=GoToEvent(url='/warehouse/wildberries'),
                    active='startswith:/warehouse/wildberries',
                ),
                c.Link(
                    components=[c.Text(text='Склад озон')],
                    on_click=GoToEvent(url='/warehouse/ozon'),
                    active='startswith:/warehouse/ozon',
                ),
                c.Link(
                    components=[c.Text(text='Склад яндекс')],
                    on_click=GoToEvent(url='/warehouse/yandex'),
                    active='startswith:/warehouse/yandex',
                ),
                c.Link(
                    components=[c.Text(text='История перемещений')],
                    on_click=GoToEvent(url='/warehouse/all_history'),
                    active='startswith:/warehouse/all_history',
                ),
                c.Link(
                    components=[c.Text(text='Создать перемещение')],
                    on_click=GoToEvent(url='/warehouse/add_movement'),
                    active='startswith:/warehouse/add_movement',
                ),

            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
    ]


@app.get('/api/orders/current', response_model=FastUI, response_model_exclude_none=True)
async def orders_view(page: int = 1) -> list[AnyComponent]:
    orders = await OrderRepository.all_orders()
    orders_full = []
    page_size = 10
    for order in orders:
        if order.status == 'Заказ не готов':
            order_object = SOrder(id=order.id, create_date=order.create_date, change_date=order.change_date,
                                  internal_article=order.internal_article,
                                  vendor_internal_article=order.vendor_internal_article, quantity_xs=order.quantity_xs,
                                  quantity_s=order.quantity_s,
                                  quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                                  color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                                  order_image=order.order_image, status=order.status,
                                  flag=order.flag)
            orders_full.append(order_object)
    orders_full.reverse()
    return main_page(
        *order_tabs(),
        c.Table(
            data=orders_full[(page - 1) * page_size: page * page_size],
            data_model=SOrder,
            columns=[
                DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='./{id}')),
                DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                DisplayLookup(field='change_date', title='Дата изменения'),
                DisplayLookup(field='internal_article', title='Внутренний артикул', mode=DisplayMode.markdown),
                DisplayLookup(field='vendor_internal_article', title='Артикул поставщика',
                              mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_xs', title='Кол-во XS', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                DisplayLookup(field='color', title='Цвет', mode=DisplayMode.markdown),
                DisplayLookup(field='shop_name', title='Название магазина', mode=DisplayMode.markdown),
                DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                DisplayLookup(field='status', title='Статус'),
                DisplayLookup(field='flag', title='Приоритет'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(orders_full)),
        title='Текущие заказы',
    )


@app.get('/api/orders/archive', response_model=FastUI, response_model_exclude_none=True)
async def orders_view(page: int = 1) -> list[AnyComponent]:
    orders = await OrderRepository.all_orders()
    orders_full = []
    page_size = 10
    for order in orders:
        if order.status == 'Заказ готов':
            order_object = SOrder(id=order.id, create_date=order.create_date, change_date=order.change_date,
                                  internal_article=order.internal_article,
                                  vendor_internal_article=order.vendor_internal_article, quantity_xs=order.quantity_xs,
                                  quantity_s=order.quantity_s,
                                  quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                                  color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                                  order_image=order.order_image, status=order.status,
                                  flag=order.flag)
            orders_full.append(order_object)
    orders_full.reverse()
    return main_page(
        *order_tabs(),
        c.Table(
            data=orders_full[(page - 1) * page_size: page * page_size],
            data_model=SOrder,
            columns=[
                DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='/orders/current/{id}')),
                DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                DisplayLookup(field='change_date', title='Дата изменения'),
                DisplayLookup(field='internal_article', title='Внутренний артикул', mode=DisplayMode.markdown),
                DisplayLookup(field='vendor_internal_article', title='Артикул поставщика',
                              mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_xs', title='Кол-во XS', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                DisplayLookup(field='color', title='Цвет', mode=DisplayMode.markdown),
                DisplayLookup(field='shop_name', title='Название магазина', mode=DisplayMode.markdown),
                DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                DisplayLookup(field='status', title='Статус'),
                DisplayLookup(field='flag', title='Приоритет'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(orders_full)),
        title='Архивные заказы',
    )


@app.get('/api/orders/current/{order_id}', response_model=FastUI, response_model_exclude_none=True)
async def order_view(order_id: int, page: int = 1) -> list[AnyComponent]:
    order = await OrderRepository.get_order(order_id)
    shipments = await ShipmentRepository.all_shipments()
    shipments_full = []
    shipment_xs = 0
    shipment_s = 0
    shipment_m = 0
    shipment_l = 0
    page_size = 10
    img_path = order.order_image
    with open(img_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    image_component = c.Image(
        src=f'data:image/png;base64,{encoded_image}',
        alt='Local Image',
        loading='lazy',
        referrer_policy='no-referrer',
        class_name='border rounded',
        width=640,
        height=640,
    )
    for shipment in shipments:
        if shipment.order_id == order_id:
            shipment_object = SShipment(id=shipment.id, order_id=shipment.order_id, create_date=shipment.create_date,
                                        change_date=shipment.change_date, quantity_xs=shipment.quantity_xs,
                                        quantity_s=shipment.quantity_s,
                                        quantity_m=shipment.quantity_m, quantity_l=shipment.quantity_l,
                                        status=shipment.status,
                                        sending_method=shipment.sending_method, sack_number=shipment.sack_number,
                                        fish=shipment.fish, cheque=shipment.cheque,
                                        document_1_id=shipment.document_1_id,
                                        document_2_id=shipment.document_2_id,
                                        image_1_id=shipment.image_1_id, image_2_id=shipment.image_2_id)
            shipments_full.append(shipment_object)
    shipments_full.reverse()
    for shipment in shipments:
        if shipment.order_id == order_id:
            shipment_xs += shipment.quantity_xs
            shipment_s += shipment.quantity_s
            shipment_m += shipment.quantity_m
            shipment_l += shipment.quantity_l
    remain_xs = order.quantity_xs - shipment_xs
    remain_s = order.quantity_s - shipment_s
    remain_m = order.quantity_m - shipment_m
    remain_l = order.quantity_l - shipment_l

    order_object = SOrder(id=order.id, create_date=order.create_date, change_date=order.change_date,
                          internal_article=order.internal_article,
                          vendor_internal_article=order.vendor_internal_article, quantity_xs=order.quantity_xs,
                          quantity_s=order.quantity_s,
                          quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                          color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                          order_image=order.order_image, status=order.status,
                          flag=order.flag)
    return main_page(
        c.Div(
            components=[
                c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
                c.Heading(text=order.internal_article, level=1),
                c.Heading(
                    text=f'XS: {order.quantity_xs} S: {order.quantity_s} M: {order.quantity_m} L: {order.quantity_l}',
                    level=2),
                c.Heading(text=f'Ожидается: XS: {remain_xs} S: {remain_s} M: {remain_m} L: {remain_l}', level=2),
                image_component,
                c.Details(data=order_object, fields=[
                    DisplayLookup(field='id', title='ID'),
                    DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                    DisplayLookup(field='change_date', title='Дата изменения'),
                    DisplayLookup(field='internal_article', title='Внутренний артикул', mode=DisplayMode.markdown),
                    DisplayLookup(field='vendor_internal_article', title='Артикул поставщика',
                                  mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_xs', title='Кол-во XS', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                    DisplayLookup(field='color', title='Цвет', mode=DisplayMode.markdown),
                    DisplayLookup(field='shop_name', title='Название магазина', mode=DisplayMode.markdown),
                    DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                    DisplayLookup(field='status', title='Статус'),
                    DisplayLookup(field='flag', title='Приоритет'),
                ]),
            ]
        ),
        c.Div(
            components=[
                c.Heading(text='Поставки к заказу:'),
                c.Table(
                    data=shipments_full[(page - 1) * page_size: page * page_size],
                    data_model=SShipment,
                    columns=[
                        DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='/shipments/current/{id}')),
                        DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                        DisplayLookup(field='change_date', title='Дата изменения', mode=DisplayMode.date),
                        DisplayLookup(field='quantity_xs', title='Кол-во XS', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                        DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                        DisplayLookup(field='status', title='Статус', mode=DisplayMode.markdown),
                    ],
                ),
                c.Pagination(page=page, page_size=page_size, total=len(shipments_full))
            ]
        ),
    )


@app.post('/api/order')
async def create_order(form: Annotated[SOrderAddForm, fastui_form(SOrderAddForm)]):
    await OrderRepository.add_order(form)
    return [c.FireEvent(event=GoToEvent(url='/orders/current'))]


@app.get('/api/orders/add_order', response_model=FastUI, response_model_exclude_none=True)
async def orders_view() -> list[AnyComponent]:
    await ProductCardRepository.all_cards()
    return main_page(
        c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
        c.Heading(text='Добавление заказа', level=2),
        c.ModelForm(model=SOrderAddForm, display_mode='page', submit_url='/api/order'),
    )


@app.get('/api/shipments/current', response_model=FastUI, response_model_exclude_none=True)
async def shipments_view(page: int = 1) -> list[AnyComponent]:
    shipments = await ShipmentRepository.all_shipments()
    shipments_full = []
    page_size = 10
    for shipment in shipments:
        order = await OrderRepository.get_order(shipment.order_id)
        if order.status != 'Заказ готов':
            shipment_object = SShipment(id=shipment.id, order_id=shipment.order_id, create_date=shipment.create_date,
                                        change_date=shipment.change_date, quantity_xs=shipment.quantity_xs,
                                        quantity_s=shipment.quantity_s,
                                        quantity_m=shipment.quantity_m, quantity_l=shipment.quantity_l,
                                        status=shipment.status,
                                        sending_method=shipment.sending_method, sack_number=shipment.sack_number,
                                        fish=shipment.fish, cheque=shipment.cheque,
                                        document_1_id=shipment.document_1_id,
                                        document_2_id=shipment.document_2_id,
                                        image_1_id=shipment.image_1_id, image_2_id=shipment.image_2_id)
            shipments_full.append(shipment_object)
    shipments_full.reverse()
    return main_page(
        *shipment_tabs(),
        c.Table(
            data=shipments_full[(page - 1) * page_size: page * page_size],
            data_model=SShipment,
            columns=[
                DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='./{id}')),
                DisplayLookup(field='order_id', title='ID заказа'),
                DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                DisplayLookup(field='change_date', title='Дата изменения'),
                DisplayLookup(field='quantity_xs', title='Кол-во XS', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                DisplayLookup(field='status', title='Статус'),
                # DisplayLookup(field='cheque', title='ID Чека'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(shipments_full)),
        title='Список поставок',
    )


@app.get('/api/shipments/current/{shipment_id}', response_model=FastUI, response_model_exclude_none=True)
async def incomes_view(shipment_id: int, page: int = 1) -> list[AnyComponent]:
    shipment = await ShipmentRepository.get_shipment(shipment_id)
    order = await OrderRepository.get_order(shipment.order_id)
    cheque = await ChequeRepository.get_cheque(shipment.cheque)
    fish = await FishRepository.get_fish(shipment.fish)
    page_size = 10

    img_path = order.order_image
    with open(img_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    order_image_component = c.Image(
        src=f'data:image/png;base64,{encoded_image}',
        alt='Local Image',
        loading='lazy',
        referrer_policy='no-referrer',
        class_name='border rounded',
        width=640,
        height=640,
    )
    img_path = cheque.cheque_image_id
    with open(img_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    cheque_image_component = c.Image(
        src=f'data:image/png;base64,{encoded_image}',
        alt='Local Image',
        loading='lazy',
        referrer_policy='no-referrer',
        class_name='border rounded',
        width=640,
        height=640,
    )
    img_path = fish.fish_image_id
    with open(img_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    fish_image_component = c.Image(
        src=f'data:image/png;base64,{encoded_image}',
        alt='Local Image',
        loading='lazy',
        referrer_policy='no-referrer',
        class_name='border rounded',
        width=640,
        height=640,
    )

    cheque_object = SCheque(id=cheque.id, shipment_id=cheque.shipment_id, order_id=cheque.order_id, date=cheque.date,
                            create_date=cheque.create_date, shop_name=cheque.shop_name,
                            cheque_number=cheque.cheque_number,
                            vendor_internal_article=cheque.vendor_internal_article, price=cheque.price,
                            cheque_image_id=cheque.cheque_image_id, cheque_status=cheque.cheque_status,
                            payment_image=cheque.payment_image)

    fish_object = SFish(id=fish.id, shipment_id=fish.shipment_id, order_id=fish.order_id, fish_number=fish.fish_number,
                        fish_date=fish.fish_date, weight=fish.weight, sack_count=fish.sack_count,
                        sending_method=fish.sending_method,
                        fish_image_id=fish.fish_image_id)

    shipment_object = SShipment(id=shipment.id, order_id=shipment.order_id, create_date=shipment.create_date,
                                change_date=shipment.change_date, quantity_xs=shipment.quantity_xs,
                                quantity_s=shipment.quantity_s,
                                quantity_m=shipment.quantity_m, quantity_l=shipment.quantity_l,
                                status=shipment.status,
                                sending_method=shipment.sending_method, sack_number=shipment.sack_number,
                                fish=shipment.fish, cheque=shipment.cheque,
                                document_1_id=shipment.document_1_id,
                                document_2_id=shipment.document_2_id,
                                image_1_id=shipment.image_1_id, image_2_id=shipment.image_2_id)
    return main_page(
        c.Div(
            components=[
                c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
                c.Heading(text='Поставка', level=1),
                c.Heading(text=f'S: {shipment.quantity_s} M: {shipment.quantity_m} L: {shipment.quantity_l}', level=2),
                c.Details(data=shipment_object, fields=[
                    # DisplayLookup(field='id', title='ID'),
                    DisplayLookup(field='order_id', title='ID заказа',
                                  on_click=GoToEvent(url='/orders/current/{order_id}')),
                    DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                    DisplayLookup(field='change_date', title='Дата изменения'),
                    DisplayLookup(field='quantity_xs', title='Кол-во XS', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                    DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                    DisplayLookup(field='status', title='Статус'),
                ]),
            ]
        ),
        c.Div(
            components=[
                c.Heading(text='Чек:'),
                c.Details(data=cheque_object, fields=[
                    # DisplayLookup(field='id', title='ID'),
                    DisplayLookup(field='date', title='Дата чека'),
                    DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                    DisplayLookup(field='shop_name', title='Название магазина'),
                    DisplayLookup(field='cheque_number', title='Номер чека', mode=DisplayMode.markdown),
                    DisplayLookup(field='vendor_internal_article', title='Внутренний артикул поставщика',
                                  mode=DisplayMode.markdown),
                    DisplayLookup(field='price', title='Цена', mode=DisplayMode.markdown),
                    DisplayLookup(field='cheque_status', title='Статус чека', mode=DisplayMode.markdown),
                ]),
            ]
        ),
        c.Div(
            components=[
                c.Heading(text='FIS`:'),
                c.Details(data=fish_object, fields=[
                    # DisplayLookup(field='id', title='ID'),
                    DisplayLookup(field='fish_number', title='Номер фиша', mode=DisplayMode.as_title),
                    DisplayLookup(field='fish_date', title='Дата фиша', mode=DisplayMode.date),
                    DisplayLookup(field='weight', title='Вес'),
                    DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                ]),
            ]
        ),
        order_image_component,
        cheque_image_component,
        fish_image_component,
    )


@app.get('/api/cheques/fire', response_model=FastUI, response_model_exclude_none=True)
async def fire_cheques(page: int = 1) -> list[AnyComponent]:
    cheques = await ChequeRepository.all_cheques()
    cheques_full = []
    page_size = 10
    for cheque in cheques:
        if cheque.cheque_status == 'Чек не оплачен по истечению 2-ух недель':
            cheque_object = SCheque(id=cheque.id, shipment_id=cheque.shipment_id, order_id=cheque.order_id,
                                    date=cheque.date,
                                    create_date=cheque.create_date, shop_name=cheque.shop_name,
                                    cheque_number=cheque.cheque_number,
                                    vendor_internal_article=cheque.vendor_internal_article, price=cheque.price,
                                    cheque_image_id=cheque.cheque_image_id, cheque_status=cheque.cheque_status,
                                    payment_image=cheque.payment_image)
            cheques_full.append(cheque_object)
    cheques_full.reverse()
    return main_page(
        *cheque_tabs(),
        c.Table(
            data=cheques_full[(page - 1) * page_size: page * page_size],
            data_model=SCheque,
            columns=[
                DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='./{id}')),
                DisplayLookup(field='date', title='Дата чека'),
                DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                DisplayLookup(field='shop_name', title='Название магазина'),
                DisplayLookup(field='cheque_number', title='Номер чека', mode=DisplayMode.markdown),
                DisplayLookup(field='vendor_internal_article', title='Внутренний артикул поставщика',
                              mode=DisplayMode.markdown),
                DisplayLookup(field='price', title='Цена', mode=DisplayMode.markdown),
                DisplayLookup(field='cheque_status', title='Статус чека', mode=DisplayMode.markdown),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(cheques_full)),
        title='Горящие чеки',
    )


@app.get('/api/cheques/delay', response_model=FastUI, response_model_exclude_none=True)
async def delay_cheques(page: int = 1) -> list[AnyComponent]:
    cheques = await ChequeRepository.all_cheques()
    cheques_full = []
    page_size = 10
    for cheque in cheques:
        if cheque.cheque_status == 'По чеку имеется отсрочка':
            cheque_object = SCheque(id=cheque.id, shipment_id=cheque.shipment_id, order_id=cheque.order_id,
                                    date=cheque.date,
                                    create_date=cheque.create_date, shop_name=cheque.shop_name,
                                    cheque_number=cheque.cheque_number,
                                    vendor_internal_article=cheque.vendor_internal_article, price=cheque.price,
                                    cheque_image_id=cheque.cheque_image_id, cheque_status=cheque.cheque_status,
                                    payment_image=cheque.payment_image)
            cheques_full.append(cheque_object)
    cheques_full.reverse()
    return main_page(
        *cheque_tabs(),
        c.Table(
            data=cheques_full[(page - 1) * page_size: page * page_size],
            data_model=SCheque,
            columns=[
                DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='./{id}')),
                DisplayLookup(field='date', title='Дата чека'),
                DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                DisplayLookup(field='shop_name', title='Название магазина'),
                DisplayLookup(field='cheque_number', title='Номер чека', mode=DisplayMode.markdown),
                DisplayLookup(field='vendor_internal_article', title='Внутренний артикул поставщика',
                              mode=DisplayMode.markdown),
                DisplayLookup(field='price', title='Цена', mode=DisplayMode.markdown),
                DisplayLookup(field='cheque_status', title='Статус чека', mode=DisplayMode.markdown),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(cheques_full)),
        title='Чеки с отсрочкой',
    )


@app.get('/api/cheques/archive', response_model=FastUI, response_model_exclude_none=True)
async def archive_cheques(page: int = 1) -> list[AnyComponent]:
    cheques = await ChequeRepository.all_cheques()
    cheques_full = []
    page_size = 10
    for cheque in cheques:
        if cheque.cheque_status == 'Чек оплачен':
            cheque_object = SCheque(id=cheque.id, shipment_id=cheque.shipment_id, order_id=cheque.order_id,
                                    date=cheque.date,
                                    create_date=cheque.create_date, shop_name=cheque.shop_name,
                                    cheque_number=cheque.cheque_number,
                                    vendor_internal_article=cheque.vendor_internal_article, price=cheque.price,
                                    cheque_image_id=cheque.cheque_image_id, cheque_status=cheque.cheque_status,
                                    payment_image=cheque.payment_image)
            cheques_full.append(cheque_object)
    cheques_full.reverse()
    return main_page(
        *cheque_tabs(),
        c.Table(
            data=cheques_full[(page - 1) * page_size: page * page_size],
            data_model=SCheque,
            columns=[
                DisplayLookup(field='id', title='ID'),
                DisplayLookup(field='date', title='Дата чека'),
                DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                DisplayLookup(field='shop_name', title='Название магазина'),
                DisplayLookup(field='cheque_number', title='Номер чека', mode=DisplayMode.markdown),
                DisplayLookup(field='vendor_internal_article', title='Внутренний артикул поставщика',
                              mode=DisplayMode.markdown),
                DisplayLookup(field='price', title='Цена', mode=DisplayMode.markdown),
                DisplayLookup(field='cheque_status', title='Статус чека', mode=DisplayMode.markdown),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(cheques_full)),
        title='Архив чеков',
    )


@app.get('/api/cheques/fire/{cheque_id}', response_model=FastUI, response_model_exclude_none=True)
async def incomes_view(cheque_id: int, page: int = 1) -> list[AnyComponent]:
    cheque = await ChequeRepository.get_cheque(cheque_id)
    page_size = 10

    cheque_object = SCheque(id=cheque.id, shipment_id=cheque.shipment_id, order_id=cheque.order_id, date=cheque.date,
                            create_date=cheque.create_date, shop_name=cheque.shop_name,
                            cheque_number=cheque.cheque_number,
                            vendor_internal_article=cheque.vendor_internal_article, price=cheque.price,
                            cheque_image_id=cheque.cheque_image_id, cheque_status=cheque.cheque_status,
                            payment_image=cheque.payment_image)
    return main_page(
        c.Div(
            components=[
                c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
                c.Heading(text='Чек:'),
                c.Details(data=cheque_object, fields=[
                    # DisplayLookup(field='id', title='ID'),
                    DisplayLookup(field='date', title='Дата чека'),
                    DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                    DisplayLookup(field='shop_name', title='Название магазина'),
                    DisplayLookup(field='cheque_number', title='Номер чека', mode=DisplayMode.markdown),
                    DisplayLookup(field='vendor_internal_article', title='Внутренний артикул поставщика',
                                  mode=DisplayMode.markdown),
                    DisplayLookup(field='price', title='Цена', mode=DisplayMode.markdown),
                    DisplayLookup(field='cheque_status', title='Статус чека', mode=DisplayMode.markdown),
                ]),
            ]
        ),
    )


@app.get('/api/cheques/delay/{cheque_id}', response_model=FastUI, response_model_exclude_none=True)
async def incomes_view(cheque_id: int, page: int = 1) -> list[AnyComponent]:
    cheque = await ChequeRepository.get_cheque(cheque_id)
    page_size = 10

    img_path = cheque.cheque_image_id
    with open(img_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    image_component = c.Image(
        src=f'data:image/png;base64,{encoded_image}',
        alt='Local Image',
        loading='lazy',
        referrer_policy='no-referrer',
        class_name='border rounded',
        width=640,
        height=640,
    )
    cheque_object = SCheque(id=cheque.id, shipment_id=cheque.shipment_id, order_id=cheque.order_id, date=cheque.date,
                            create_date=cheque.create_date, shop_name=cheque.shop_name,
                            cheque_number=cheque.cheque_number,
                            vendor_internal_article=cheque.vendor_internal_article, price=cheque.price,
                            cheque_image_id=cheque.cheque_image_id, cheque_status=cheque.cheque_status,
                            payment_image=cheque.payment_image)
    return main_page(
        c.Div(
            components=[
                c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
                c.Heading(text='Чек:'),
                image_component,
                c.Details(data=cheque_object, fields=[
                    # DisplayLookup(field='id', title='ID'),
                    DisplayLookup(field='date', title='Дата чека'),
                    DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                    DisplayLookup(field='shop_name', title='Название магазина'),
                    DisplayLookup(field='cheque_number', title='Номер чека', mode=DisplayMode.markdown),
                    DisplayLookup(field='vendor_internal_article', title='Внутренний артикул поставщика',
                                  mode=DisplayMode.markdown),
                    DisplayLookup(field='price', title='Цена', mode=DisplayMode.markdown),
                    DisplayLookup(field='cheque_status', title='Статус чека', mode=DisplayMode.markdown),
                ]),
            ]
        ),
    )


@app.get('/api/warehouse/logist', response_model=FastUI, response_model_exclude_none=True)
async def articles_view(page: int = 1) -> list[AnyComponent]:
    articles = await LogistWarehouseRepository.all_articles()
    articles_full = []
    page_size = 10
    for article in articles:
        shipment_object = SWarehouse(article=article.article, quantity_xs=article.quantity_xs,
                                     quantity_s=article.quantity_s, quantity_m=article.quantity_m,
                                     quantity_l=article.quantity_l)
        articles_full.append(shipment_object)
    return main_page(
        *warehouse_tabs(),
        c.Table(
            data=articles_full[(page - 1) * page_size: page * page_size],
            data_model=SWarehouse,
            columns=[
                DisplayLookup(field='article', title='Артикул'),
                DisplayLookup(field='quantity_xs', title='Кол-во XS'),
                DisplayLookup(field='quantity_s', title='Кол-во S'),
                DisplayLookup(field='quantity_m', title='Кол-во M'),
                DisplayLookup(field='quantity_l', title='Кол-во L'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(articles_full)),
        title='Кол-во товаров на складе логистов',
    )


@app.get('/api/warehouse/fullfilment', response_model=FastUI, response_model_exclude_none=True)
async def articles_view(page: int = 1) -> list[AnyComponent]:
    articles = await FullfilmentWarehouseRepository.all_articles()
    articles_full = []
    page_size = 10
    for article in articles:
        shipment_object = SWarehouse(article=article.article, quantity_xs=article.quantity_xs,
                                     quantity_s=article.quantity_s, quantity_m=article.quantity_m,
                                     quantity_l=article.quantity_l)
        articles_full.append(shipment_object)
    return main_page(
        *warehouse_tabs(),
        c.Table(
            data=articles_full[(page - 1) * page_size: page * page_size],
            data_model=SWarehouse,
            columns=[
                DisplayLookup(field='article', title='Артикул'),
                DisplayLookup(field='quantity_xs', title='Кол-во XS'),
                DisplayLookup(field='quantity_s', title='Кол-во S'),
                DisplayLookup(field='quantity_m', title='Кол-во M'),
                DisplayLookup(field='quantity_l', title='Кол-во L'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(articles_full)),
        title='Кол-во товаров на складе фуллфилмент',
    )


@app.get('/api/warehouse/wildberries', response_model=FastUI, response_model_exclude_none=True)
async def articles_view(page: int = 1) -> list[AnyComponent]:
    articles = await WildberriesWarehouseRepository.all_articles()
    articles_full = []
    page_size = 10
    for article in articles:
        shipment_object = SWarehouse(article=article.article, quantity_xs=article.quantity_xs,
                                     quantity_s=article.quantity_s, quantity_m=article.quantity_m,
                                     quantity_l=article.quantity_l)
        articles_full.append(shipment_object)
    return main_page(
        *warehouse_tabs(),
        c.Table(
            data=articles_full[(page - 1) * page_size: page * page_size],
            data_model=SWarehouse,
            columns=[
                DisplayLookup(field='article', title='Артикул'),
                DisplayLookup(field='quantity_xs', title='Кол-во XS'),
                DisplayLookup(field='quantity_s', title='Кол-во S'),
                DisplayLookup(field='quantity_m', title='Кол-во M'),
                DisplayLookup(field='quantity_l', title='Кол-во L'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(articles_full)),
        title='Кол-во товаров на складе WB',
    )


@app.get('/api/warehouse/ozon', response_model=FastUI, response_model_exclude_none=True)
async def articles_view(page: int = 1) -> list[AnyComponent]:
    articles = await OzonWarehouseRepository.all_articles()
    articles_full = []
    page_size = 10
    for article in articles:
        shipment_object = SWarehouse(article=article.article, quantity_xs=article.quantity_xs,
                                     quantity_s=article.quantity_s, quantity_m=article.quantity_m,
                                     quantity_l=article.quantity_l)
        articles_full.append(shipment_object)
    return main_page(
        *warehouse_tabs(),
        c.Table(
            data=articles_full[(page - 1) * page_size: page * page_size],
            data_model=SWarehouse,
            columns=[
                DisplayLookup(field='article', title='Артикул'),
                DisplayLookup(field='quantity_xs', title='Кол-во XS'),
                DisplayLookup(field='quantity_s', title='Кол-во S'),
                DisplayLookup(field='quantity_m', title='Кол-во M'),
                DisplayLookup(field='quantity_l', title='Кол-во L'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(articles_full)),
        title='Кол-во товаров на складе ozon',
    )


@app.get('/api/warehouse/yandex', response_model=FastUI, response_model_exclude_none=True)
async def articles_view(page: int = 1) -> list[AnyComponent]:
    articles = await YandexWarehouseRepository.all_articles()
    articles_full = []
    page_size = 10
    for article in articles:
        shipment_object = SWarehouse(article=article.article, quantity_xs=article.quantity_xs,
                                     quantity_s=article.quantity_s, quantity_m=article.quantity_m,
                                     quantity_l=article.quantity_l)
        articles_full.append(shipment_object)
    return main_page(
        *warehouse_tabs(),
        c.Table(
            data=articles_full[(page - 1) * page_size: page * page_size],
            data_model=SWarehouse,
            columns=[
                DisplayLookup(field='article', title='Артикул'),
                DisplayLookup(field='quantity_xs', title='Кол-во XS'),
                DisplayLookup(field='quantity_s', title='Кол-во S'),
                DisplayLookup(field='quantity_m', title='Кол-во M'),
                DisplayLookup(field='quantity_l', title='Кол-во L'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(articles_full)),
        title='Кол-во товаров на складе yandex',
    )


@app.get('/api/warehouse/add_movement', response_model=FastUI, response_model_exclude_none=True)
async def orders_view() -> list[AnyComponent]:
    await ProductCardRepository.all_cards()
    return main_page(
        c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
        c.Heading(text='Создать перемещение', level=2),
        c.ModelForm(model=SWarehouseMovementForm, display_mode='page', submit_url='/api/move'),
    )


@app.post('/api/move', response_model=FastUI, response_model_exclude_none=True)
async def select_form_post(form: Annotated[SWarehouseMovementForm, patched_fastui_form(SWarehouseMovementForm)]):
    print(form.file.filename.encode("utf-8"))
    print(form.comment)
    print(form)
    r = {}
    if form.file.filename != '' and form.file.size > 0:
        upload_directory = "uploads"
        os.makedirs(upload_directory, exist_ok=True)

        file_content = await form.file.read()

        file_path = os.path.join(upload_directory, form.file.filename)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        await form.file.close()

        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'credentials.json'
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        folder_id = '1icsnYtbMyif_yjQUy4xAMad8HVUcN3Or'
        name = form.file.filename
        file_metadata = {
            'name': name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        r = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    async with async_session() as session:

        flag = False
        date_now_object = datetime.now()
        formatted_date = date_now_object.strftime("%d.%m.%Y %H:%M:%S")
        if (form.start.value == 'Склад логистов' or form.destination.value == 'Склад логистов'):
            result = await session.execute(
                select(LogistWarehouse).where(LogistWarehouse.article == form.article.value)
            )
            product = result.scalar_one_or_none()
            if (form.start.value == 'Склад логистов' and product):
                if ((product.quantity_xs >= form.quantity_xs and product.quantity_s >= form.quantity_s
                     and product.quantity_m >= form.quantity_m and product.quantity_l >= form.quantity_l)):
                    flag = True
                    product.quantity_xs -= form.quantity_xs
                    product.quantity_s -= form.quantity_s
                    product.quantity_m -= form.quantity_m
                    product.quantity_l -= form.quantity_l
            if (form.destination.value == 'Склад логистов' and flag == True):
                if product:

                    product.quantity_xs += form.quantity_xs
                    product.quantity_s += form.quantity_s
                    product.quantity_m += form.quantity_m
                    product.quantity_l += form.quantity_l

                    if form.file.filename != '' and form.file.size > 0:

                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)

                    session.add(new_moving)
                else:
                    new_product = LogistWarehouse(article=form.article.value, quantity_xs=form.quantity_xs,
                                                  quantity_s=form.quantity_s, quantity_m=form.quantity_m,
                                                  quantity_l=form.quantity_l)
                    session.add(new_product)
                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)

                    session.add(new_moving)

        if (form.start.value == 'Склад фуллфилмент' or form.destination.value == 'Склад фуллфилмент'):
            result = await session.execute(
                select(FullfilmenttWarehouse).where(FullfilmenttWarehouse.article == form.article.value)
            )
            product = result.scalar_one_or_none()
            if (form.start.value == 'Склад фуллфилмент' and product):
                if ((product.quantity_xs >= form.quantity_xs and product.quantity_s >= form.quantity_s
                     and product.quantity_m >= form.quantity_m and product.quantity_l >= form.quantity_l)):
                    flag = True
                    product.quantity_xs -= form.quantity_xs
                    product.quantity_s -= form.quantity_s
                    product.quantity_m -= form.quantity_m
                    product.quantity_l -= form.quantity_l
            if (form.destination.value == 'Склад фуллфилмент' and flag == True):
                if product:
                    product.quantity_xs += form.quantity_xs
                    product.quantity_s += form.quantity_s
                    product.quantity_m += form.quantity_m
                    product.quantity_l += form.quantity_l

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
                else:
                    new_product = FullfilmenttWarehouse(article=form.article.value, quantity_xs=form.quantity_xs,
                                                        quantity_s=form.quantity_s, quantity_m=form.quantity_m,
                                                        quantity_l=form.quantity_l)
                    session.add(new_product)

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
        if (form.start.value == 'Склад wildberries' or form.destination.value == 'Склад wildberries'):
            result = await session.execute(
                select(WildberriesWarehouse).where(WildberriesWarehouse.article == form.article.value)
            )
            product = result.scalar_one_or_none()

            if (form.start.value == 'Склад wildberries' and product):
                if ((product.quantity_xs >= form.quantity_xs and product.quantity_s >= form.quantity_s
                     and product.quantity_m >= form.quantity_m and product.quantity_l >= form.quantity_l)):
                    flag = True
                    product.quantity_xs -= form.quantity_xs
                    product.quantity_s -= form.quantity_s
                    product.quantity_m -= form.quantity_m
                    product.quantity_l -= form.quantity_l
            if (form.destination.value == 'Склад wildberries' and flag == True):
                if product:
                    product.quantity_xs += form.quantity_xs
                    product.quantity_s += form.quantity_s
                    product.quantity_m += form.quantity_m
                    product.quantity_l += form.quantity_l

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
                else:
                    new_product = WildberriesWarehouse(article=form.article.value, quantity_xs=form.quantity_xs,
                                                       quantity_s=form.quantity_s, quantity_m=form.quantity_m,
                                                       quantity_l=form.quantity_l)
                    session.add(new_product)

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
        if (form.start.value == 'Склад ozon' or form.destination.value == 'Склад ozon'):
            result = await session.execute(
                select(OzonWarehouse).where(OzonWarehouse.article == form.article.value)
            )
            product = result.scalar_one_or_none()
            if (form.start.value == 'Склад ozon' and product):
                if ((product.quantity_xs >= form.quantity_xs and product.quantity_s >= form.quantity_s
                     and product.quantity_m >= form.quantity_m and product.quantity_l >= form.quantity_l)):
                    flag = True
                    product.quantity_xs -= form.quantity_xs
                    product.quantity_s -= form.quantity_s
                    product.quantity_m -= form.quantity_m
                    product.quantity_l -= form.quantity_l
            if (form.destination.value == 'Склад ozon' and flag == True):
                if product:
                    product.quantity_xs += form.quantity_xs
                    product.quantity_s += form.quantity_s
                    product.quantity_m += form.quantity_m
                    product.quantity_l += form.quantity_l

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
                else:
                    new_product = OzonWarehouse(article=form.article.value, quantity_xs=form.quantity_xs,
                                                quantity_s=form.quantity_s, quantity_m=form.quantity_m,
                                                quantity_l=form.quantity_l)
                    session.add(new_product)

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
        if (form.start.value == 'Склад yandex' or form.destination.value == 'Склад yandex'):
            result = await session.execute(
                select(YandexWarehouse).where(YandexWarehouse.article == form.article.value)
            )
            product = result.scalar_one_or_none()
            if (form.start.value == 'Склад yandex' and product):
                if ((product.quantity_xs >= form.quantity_xs and product.quantity_s >= form.quantity_s
                     and product.quantity_m >= form.quantity_m and product.quantity_l >= form.quantity_l)):
                    flag = True
                    product.quantity_xs -= form.quantity_xs
                    product.quantity_s -= form.quantity_s
                    product.quantity_m -= form.quantity_m
                    product.quantity_l -= form.quantity_l
            if (form.destination.value == 'Склад yandex' and flag == True):
                if product:
                    product.quantity_xs += form.quantity_xs
                    product.quantity_s += form.quantity_s
                    product.quantity_m += form.quantity_m
                    product.quantity_l += form.quantity_l

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
                else:
                    new_product = YandexWarehouse(article=form.article.value, quantity_xs=form.quantity_xs,
                                                  quantity_s=form.quantity_s, quantity_m=form.quantity_m,
                                                  quantity_l=form.quantity_l)
                    session.add(new_product)

                    if form.file.filename != '' and form.file.size > 0:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment, file=r['id'])
                    else:
                        new_moving = MovementHistory(start=form.start.value, destination=form.destination.value,
                                                     article=form.article.value, time=formatted_date,
                                                     quantity_xs=form.quantity_xs, quantity_s=form.quantity_s,
                                                     quantity_m=form.quantity_m, quantity_l=form.quantity_l,
                                                     comment=form.comment)
                    session.add(new_moving)
        await session.commit()

    if (form.destination.value == 'Склад фуллфилмент'):
        return [c.FireEvent(event=GoToEvent(url='/warehouse/fullfilment'))]
    elif (form.destination.value == 'Склад wildberries'):
        return [c.FireEvent(event=GoToEvent(url='/warehouse/wildberries'))]
    elif (form.destination.value == 'Склад ozon'):
        return [c.FireEvent(event=GoToEvent(url='/warehouse/ozon'))]
    elif (form.destination.value == 'Склад yandex'):
        return [c.FireEvent(event=GoToEvent(url='/warehouse/yandex'))]
    else:
        return [c.FireEvent(event=GoToEvent(url='/'))]


@app.get("/api/files/{file_name}", response_model=FastUI, response_model_exclude_none=True)
async def download_file(file_name: str):
    print(file_name)
    file_path = Path("uploads") / file_name
    print(file_path)
    print(os.path.exists(file_path))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)


def download_file_from_history(file_name):
    file_path = os.path.join("/uploads", file_name)
    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)


@app.get('/api/warehouse/all_history', response_model=FastUI, response_model_exclude_none=True)
async def history_view(page: int = 1) -> list[AnyComponent]:
    history_moving = await HistoryWarehouseRepository.all_history()
    history_full = []
    page_size = 10
    for history in history_moving:
        history_object = SWarehouseMovementHistory(id=history.id, start=history.start,
                                                   article=history.article, time=history.time,
                                                   destination=history.destination, quantity_xs=history.quantity_xs,
                                                   quantity_s=history.quantity_s, quantity_m=history.quantity_m,
                                                   quantity_l=history.quantity_l, file=history.file,
                                                   comment=history.comment)
        print(history.file)
        history_full.append(history_object)

    return main_page(
        *warehouse_tabs(),
        c.Table(
            data=history_full[(page - 1) * page_size: page * page_size],
            data_model=SWarehouseMovementHistory,
            columns=[

                DisplayLookup(field='id', title='ID', on_click=GoToEvent(url="./{id}")),
                DisplayLookup(field='article', title='Артикул'),
                DisplayLookup(field='time', title='Время'),
                DisplayLookup(field='start', title='Склад откуда отправили'),
                DisplayLookup(field='destination', title='Склад куда отправили'),
                DisplayLookup(field='quantity_xs', title='Кол-во XS'),
                DisplayLookup(field='quantity_s', title='Кол-во S'),
                DisplayLookup(field='quantity_m', title='Кол-во M'),
                DisplayLookup(field='quantity_l', title='Кол-во L'),
                DisplayLookup(field='file',
                              title='Файл',
                              on_click=GoToEvent(url="https://drive.google.com/uc?export=download&id={file}"),

                              ),

                DisplayLookup(field='comment', title='Комментарий'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(history_full)),
        title='История перемещений',
    )


@app.get('/api/warehouse/all_history/{history_id}', response_model=FastUI, response_model_exclude_none=True)
async def history_id_view(history_id: int, page: int = 1) -> list[AnyComponent]:
    history = await HistoryWarehouseRepository.get_history(history_id)

    history_object = SWarehouseMovementHistory(id=history.id, start=history.start, destination=history.destination,
                                               article=history.article, time=history.time,
                                               quantity_xs=history.quantity_xs, quantity_s=history.quantity_s,
                                               quantity_m=history.quantity_m,
                                               quantity_l=history.quantity_l, file=history.file,
                                               comment=history.comment)
    if (history_object.file != None):
        return main_page(
            c.Div(
                components=[
                    c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
                    c.Heading(text=f'Артикул: {history_object.article}', level=1),
                    c.Heading(text=f'Время: {history_object.time}', level=1),
                    c.Heading(text=f'Склад откуда отправлено: {history_object.start}', level=1),
                    c.Heading(text=f'Склад куда отправлено: {history_object.destination}', level=1),

                    c.Heading(
                        text=f'Количество единиц: XS: {history_object.quantity_xs} S: {history_object.quantity_s} M: {history_object.quantity_m} L: {history_object.quantity_l}',
                        level=2),
                    c.Heading(text=f'Комментарий: {history_object.comment}', level=1),
                    c.Link(
                        components=[c.Heading(text=f'Файл', level=1)],
                        on_click=GoToEvent(url=f'https://drive.google.com/uc?export=download&id={history_object.file}'),
                    ),
                ],
            ),
        )
    else:
        return main_page(
            c.Div(
                components=[
                    c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
                    c.Heading(text=f'Артикул: {history_object.article}', level=1),
                    c.Heading(text=f'Время: {history_object.time}', level=1),
                    c.Heading(text=f'Склад откуда отправлено: {history_object.start}', level=1),
                    c.Heading(text=f'Склад куда отправлено: {history_object.destination}', level=1),

                    c.Heading(
                        text=f'Количество единиц: XS: {history_object.quantity_xs} S: {history_object.quantity_s} M: {history_object.quantity_m} L: {history_object.quantity_l}',
                        level=2),
                    c.Heading(text=f'Комментарий: {history_object.comment}', level=1),
                    c.ModelForm(model=SWarehouseMovementAddFileForm, display_mode='page',
                                submit_url=f'./add_file/{history_id}'),

                ],
            ),
        )


@app.post('/warehouse/all_history/add_file/{history_id}', response_model=FastUI, response_model_exclude_none=True)
async def select_form_post(history_id: int, form: Annotated[
    SWarehouseMovementAddFileForm, patched_fastui_form(SWarehouseMovementAddFileForm)]):
    r = {}
    if form.file.filename != '' and form.file.size > 0:
        upload_directory = "uploads"
        os.makedirs(upload_directory, exist_ok=True)

        file_content = await form.file.read()

        file_path = os.path.join(upload_directory, form.file.filename)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        await form.file.close()

        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'credentials.json'
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        folder_id = '1icsnYtbMyif_yjQUy4xAMad8HVUcN3Or'
        name = form.file.filename
        file_metadata = {
            'name': name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        r = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    async with async_session() as session:
        result = await session.execute(
            select(MovementHistory).where(MovementHistory.id == history_id)
        )
        moving = result.scalar_one_or_none()

        if form.file.filename != '' and form.file.size > 0:
            moving.file = r['id']

        await session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/warehouse/all_history/{history_id}'))]


@app.get('/api/', response_model=FastUI, response_model_exclude_none=True)
async def components_view(page: int = 1) -> list[AnyComponent]:
    orders = await OrderRepository.all_orders()
    orders_full = []
    page_size = 5
    today_date = datetime.now()
    for order in orders:
        if order.status == 'Заказ не готов':
            order_date = datetime.strptime(order.create_date, '%d-%m-%Y %H:%M:%S')
            week = today_date - timedelta(days=7)
            if week <= order_date <= today_date:
                order_object = SOrder(id=order.id, create_date=order.create_date, change_date=order.change_date,
                                      internal_article=order.internal_article,
                                      vendor_internal_article=order.vendor_internal_article,
                                      quantity_xs=order.quantity_xs, quantity_s=order.quantity_s,
                                      quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                                      color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                                      order_image=order.order_image, status=order.status,
                                      flag=order.flag)
                orders_full.append(order_object)
    orders_full.reverse()
    cheques = await ChequeRepository.all_cheques()
    cheques_full = []
    for cheque in cheques:
        if cheque.cheque_status == 'Чек не оплачен по истечению 2-ух недель':
            cheque_object = SCheque(id=cheque.id, shipment_id=cheque.shipment_id, order_id=cheque.order_id,
                                    date=cheque.date,
                                    create_date=cheque.create_date, shop_name=cheque.shop_name,
                                    cheque_number=cheque.cheque_number,
                                    vendor_internal_article=cheque.vendor_internal_article, price=cheque.price,
                                    cheque_image_id=cheque.cheque_image_id, cheque_status=cheque.cheque_status,
                                    payment_image=cheque.payment_image)
            cheques_full.append(cheque_object)
    cheques_full.reverse()
    return main_page(
        c.Div(
            components=[
                c.Heading(text='Список последних заказов', level=2),
                c.Table(
                    data=orders_full[(page - 1) * page_size: page * page_size],
                    data_model=SOrder,
                    columns=[
                        DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='orders/current/{id}')),
                        DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                        DisplayLookup(field='change_date', title='Дата изменения'),
                        DisplayLookup(field='internal_article', title='Внутренний артикул', mode=DisplayMode.markdown),
                        DisplayLookup(field='vendor_internal_article', title='Артикул поставщика',
                                      mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_xs', title='Кол-во XS', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                        DisplayLookup(field='color', title='Цвет', mode=DisplayMode.markdown),
                        DisplayLookup(field='shop_name', title='Название магазина', mode=DisplayMode.markdown),
                        DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                        DisplayLookup(field='status', title='Статус'),
                        DisplayLookup(field='flag', title='Приоритет'),
                    ],
                ),
                c.Pagination(page=page, page_size=page_size, total=len(orders_full)),
            ],
            class_name='card-container',
        ),
        c.Div(
            components=[
                c.Heading(text='Список горящих чеков', level=2),
                c.Table(
                    data=cheques_full[(page - 1) * page_size: page * page_size],
                    data_model=SCheque,
                    columns=[
                        DisplayLookup(field='id', title='ID', on_click=GoToEvent(url='cheques/fire/{id}')),
                        DisplayLookup(field='date', title='Дата чека'),
                        DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                        DisplayLookup(field='shop_name', title='Название магазина'),
                        DisplayLookup(field='cheque_number', title='Номер чека', mode=DisplayMode.markdown),
                        DisplayLookup(field='vendor_internal_article', title='Внутренний артикул поставщика',
                                      mode=DisplayMode.markdown),
                        DisplayLookup(field='price', title='Цена', mode=DisplayMode.markdown),
                        DisplayLookup(field='cheque_status', title='Статус чека', mode=DisplayMode.markdown),
                    ],
                ),
                c.Pagination(page=page, page_size=page_size, total=len(cheques_full)),
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
