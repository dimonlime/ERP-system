from datetime import datetime, timedelta

from fastapi import FastAPI, Depends
import asyncio
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
import base64

from fastui.components.display import DisplayLookup, DisplayMode
from fastui.forms import fastui_form, SelectSearchResponse
from starlette.responses import HTMLResponse, FileResponse

from ODDS.parse import initial
from database import async_main, delete_tables, async_session_ODDS_
from routers.router import order_router, shipment_router, cheque_router, fish_router, ODDS_router, generate_report_ODDS
from typing import Annotated, Sequence, Union

from fastapi import APIRouter, Depends

from repository import OrderRepository, ShipmentRepository, ChequeRepository, FishRepository, ODDSRepository, \
    ProductCardRepository
from schemas.schemas import (SOrderAdd, SOrder, SOrderId, SShipment, SShipmentAdd, SShipmentId, SChequeAdd, SCheque,
                             SChequeId,
                             SFish, SFishAdd, SFishId, ReportODDSRequest, SODDSpayment, SODDSincome, BasePaymentIncome,
                             SODDSFilterForm,
                             SFish, SFishAdd, SFishId, SOrderAddForm)

from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.events import GoToEvent, PageEvent, BackEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(job_parse_api_modulbank, 'interval', hours=5)
    scheduler.start()
    # await delete_tables()
    # print('База очищена')
    #await async_main()
    #print('База готова к работе')
    yield
    print('Выключение')


app = FastAPI(lifespan=lifespan)
app.include_router(order_router)
app.include_router(shipment_router)
app.include_router(cheque_router)
app.include_router(fish_router)
app.include_router(ODDS_router)

scheduler = AsyncIOScheduler()

async def job_parse_api_modulbank():
    logger.info("Задача парс апи модульбанка запущена")
    await initial()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

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
                #c.Link(
                 #   components=[c.Text(text='Информация по артикулам')],
                  #  on_click=GoToEvent(url='/article_info'),
                   # active='startswith:/article_info',
                #),
                c.Link(
                    components=[c.Text(text='Отчет ОДДС')],
                    on_click=GoToEvent(url='/odds/all'),
                    active='startswith:/odds/all',
                )

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

def ODDS_tabs() -> list[AnyComponent]:
    return [
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Общий')],
                    on_click=GoToEvent(url='/odds/all'),
                    active='startswith:/odds/all',
                ),
                c.Link(
                    components=[c.Text(text='Платежи')],
                    on_click=GoToEvent(url='/odds/payments'),
                    active='startswith:/odds/payments',
                ),
                c.Link(
                    components=[c.Text(text='Поступления')],
                    on_click=GoToEvent(url='/odds/incomes'),
                    active='startswith:/odds/incomes',
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


@app.get('/api/orders/current', response_model=FastUI, response_model_exclude_none=True)
async def orders_view(page: int = 1) -> list[AnyComponent]:
    orders = await OrderRepository.all_orders()
    orders_full = []
    page_size = 10
    for order in orders:
        if order.status == 'Заказ не готов':
            order_object = SOrder(id=order.id, create_date=order.create_date, change_date=order.change_date,
                                  internal_article=order.internal_article,
                                  vendor_internal_article=order.vendor_internal_article, quantity_s=order.quantity_s,
                                  quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                                  color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                                  order_image=order.order_image, status=order.status,
                                  flag=order.flag)
            orders_full.append(order_object)
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

@app.post("/api/odds_report")
async def odds_report(form: Annotated[ReportODDSRequest, fastui_form(ReportODDSRequest)]):
    print(f"{form=}")
    period = f"{form}"
    print(period)
    await generate_report_ODDS(request=form)
    return await download_file()
@app.get("/api/download")
def download_file():
    file_path = r"ODDS/excel_files/report_ODDS.xlsx"
    path = Path(file_path)
    return FileResponse(path, media_type='application/octet-stream', filename=path.name)



@app.get("/api/odds/all", response_model=FastUI, response_model_exclude_none=True)
async def odds_payments_and_incomes(page: int = 1, date: str | None = None) -> list[AnyComponent]:
    payments = await ODDSRepository.all_payments()
    incomes = await ODDSRepository.all_incomes()
    payments_and_incomes_full = []
    page_size = 12
    filter_form_initial = {}
    for income in incomes:

        income_object = SODDSincome(id=income.id,
                                    name=income.name,
                                    code=income.code,
                                    amount=income.amount,
                                    date=income.date)
        payments_and_incomes_full.append(income_object)
        if income.name == 'прочие поступления':

            for payment in payments:
                if income.date == payment.date:
                    payment_object = SODDSpayment(id=payment.id,
                                                  name=payment.name,
                                                  code=payment.code,
                                                  amount=payment.amount,
                                                  date=payment.date)
                    payments_and_incomes_full.append(payment_object)

    if date:
        payments_and_incomes_full = [payment for payment in payments_and_incomes_full if payment.date == date]
        period = payments_and_incomes_full[0].date if payments_and_incomes_full else None
        filter_form_initial['date'] = {'value': date, 'label': period}


    return main_page(
        *ODDS_tabs(),
        c.ModelForm(
            model=SODDSFilterForm,
            submit_url='.',
            initial=filter_form_initial,
            method='GOTO',
            submit_on_change=True,
            display_mode='inline',
        ),
        c.Table(
            data=payments_and_incomes_full[(page - 1) * page_size: page * page_size],
            data_model=BasePaymentIncome,
            columns=[
                DisplayLookup(field='id', title='ID', mode=DisplayMode.markdown),
                DisplayLookup(field='name', title='Описание', mode=DisplayMode.markdown),
                DisplayLookup(field='code', title='Код', mode=DisplayMode.markdown),
                DisplayLookup(field='amount', title='Сумма', mode=DisplayMode.markdown),
                DisplayLookup(field='date', title='За период', mode=DisplayMode.markdown),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(payments_and_incomes_full)),
        title='Отчет ОДДС',
    )

@app.get('/api/odds/payments', response_model=FastUI, response_model_exclude_none=True)
async def odds_payments_view(page: int = 1, date: str | None = None) -> list[AnyComponent]:
    payments = await ODDSRepository.all_payments()
    payments_full = []
    page_size = 9
    filter_form_initial = {}
    for payment in payments:
        payment_obj = SODDSpayment(id=payment.id,
                                   name=payment.name,
                                   code=payment.code,
                                   amount=payment.amount,
                                   date=payment.date)
        payments_full.append(payment_obj)
    if date:
        payments_full = [payment for payment in payments_full if payment.date == date]
        period = payments_full[0].date if payments_full else None
        filter_form_initial['date'] = {'value': date, 'label': period}
    return main_page(
        *ODDS_tabs(),
        c.ModelForm(
            model=SODDSFilterForm,
            submit_url='.',
            initial=filter_form_initial,
            method='GOTO',
            submit_on_change=True,
            display_mode='inline',
        ),
        c.Table(
            data=payments_full[(page - 1) * page_size: page * page_size],
            data_model=SODDSpayment,
            columns=[
                DisplayLookup(field='id', title='ID', mode=DisplayMode.markdown),
                DisplayLookup(field='name', title='Описание', mode=DisplayMode.markdown),
                DisplayLookup(field='code', title='Код', mode=DisplayMode.markdown),
                DisplayLookup(field='amount', title='Сумма', mode=DisplayMode.markdown),
                DisplayLookup(field='date', title='За период', mode=DisplayMode.markdown),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(payments_full)),
        title='Платежи',
    )
@app.get('/api/odds/incomes', response_model=FastUI, response_model_exclude_none=True)
async def odds_incomes_view(page: int = 1, date: str | None = None) -> list[AnyComponent]:
    incomes = await ODDSRepository.all_incomes()
    incomes_full = []
    page_size = 3
    filter_form_initial = {}
    for income in incomes:
        income_object = SODDSincome(
            id=income.id,
            name=income.name,
            code=income.code,
            amount=income.amount,
            date=income.date
        )
        incomes_full.append(income_object)
    if date:
        incomes_full = [income for income in incomes_full if income.date == date]
        period = incomes_full[0].date if incomes_full else None
        filter_form_initial['date'] = {'value': date, 'label': period}
    return main_page(
        *ODDS_tabs(),
        c.ModelForm(
            model=SODDSFilterForm,
            submit_url='.',
            initial=filter_form_initial,
            method='GOTO',
            submit_on_change=True,
            display_mode='inline',
        ),
        c.Table(
            data=incomes_full[(page - 1) * page_size: page * page_size],
            data_model=SODDSincome,
            columns=[
                DisplayLookup(field='id', title='ID', mode=DisplayMode.markdown),
                DisplayLookup(field='name', title='Описание', mode=DisplayMode.markdown),
                DisplayLookup(field='code', title='Код', mode=DisplayMode.markdown),
                DisplayLookup(field='amount', title='Сумма', mode=DisplayMode.markdown),
                DisplayLookup(field='date', title='За период', mode=DisplayMode.markdown),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(incomes_full)),
        title='Поступления',
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
                                  vendor_internal_article=order.vendor_internal_article, quantity_s=order.quantity_s,
                                  quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                                  color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                                  order_image=order.order_image, status=order.status,
                                  flag=order.flag)
            orders_full.append(order_object)
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
                                        change_date=shipment.change_date, quantity_s=shipment.quantity_s,
                                        quantity_m=shipment.quantity_m, quantity_l=shipment.quantity_l,
                                        status=shipment.status,
                                        sending_method=shipment.sending_method, sack_number=shipment.sack_number,
                                        fish=shipment.fish, cheque=shipment.cheque,
                                        document_1_id=shipment.document_1_id,
                                        document_2_id=shipment.document_2_id,
                                        image_1_id=shipment.image_1_id, image_2_id=shipment.image_2_id)
            shipments_full.append(shipment_object)

    for shipment in shipments:
        if shipment.order_id == order_id:
            shipment_s += shipment.quantity_s
            shipment_m += shipment.quantity_m
            shipment_l += shipment.quantity_l
    remain_s = order.quantity_s - shipment_s
    remain_m = order.quantity_m - shipment_m
    remain_l = order.quantity_l - shipment_l

    order_object = SOrder(id=order.id, create_date=order.create_date, change_date=order.change_date,
                          internal_article=order.internal_article,
                          vendor_internal_article=order.vendor_internal_article, quantity_s=order.quantity_s,
                          quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                          color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                          order_image=order.order_image, status=order.status,
                          flag=order.flag)
    return main_page(
        c.Div(
            components=[
                c.Button(text='Назад', named_style='secondary', class_name='+ ms-2', on_click=BackEvent()),
                c.Heading(text=order.internal_article, level=1),
                c.Heading(text=f'S: {order.quantity_s} M: {order.quantity_m} L: {order.quantity_l}', level=2),
                c.Heading(text=f'Ожидается: S: {remain_s} M: {remain_m} L: {remain_l}', level=2),
                image_component,
                c.Details(data=order_object, fields=[
                    DisplayLookup(field='id', title='ID'),
                    DisplayLookup(field='create_date', title='Дата создания', mode=DisplayMode.date),
                    DisplayLookup(field='change_date', title='Дата изменения'),
                    DisplayLookup(field='internal_article', title='Внутренний артикул', mode=DisplayMode.markdown),
                    DisplayLookup(field='vendor_internal_article', title='Артикул поставщика',
                                  mode=DisplayMode.markdown),
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
                        DisplayLookup(field='change_date', title='Дата изменения'),
                        DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                        DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                        DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                        DisplayLookup(field='status', title='Статус'),
                        # DisplayLookup(field='fish', title='ID FIS`'),
                        # DisplayLookup(field='cheque', title='ID Чека'),
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


@app.post('/api/order/mark_order', response_model=FastUI, response_model_exclude_none=True)
async def create_order():
    print('z')
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
                                        change_date=shipment.change_date, quantity_s=shipment.quantity_s,
                                        quantity_m=shipment.quantity_m, quantity_l=shipment.quantity_l,
                                        status=shipment.status,
                                        sending_method=shipment.sending_method, sack_number=shipment.sack_number,
                                        fish=shipment.fish, cheque=shipment.cheque, document_1_id=shipment.document_1_id,
                                        document_2_id=shipment.document_2_id,
                                        image_1_id=shipment.image_1_id, image_2_id=shipment.image_2_id)
            shipments_full.append(shipment_object)
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
                DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                DisplayLookup(field='status', title='Статус'),
                # DisplayLookup(field='fish', title='ID FIS`'),
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
                                change_date=shipment.change_date, quantity_s=shipment.quantity_s,
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
                    DisplayLookup(field='quantity_s', title='Кол-во S', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_m', title='Кол-во M', mode=DisplayMode.markdown),
                    DisplayLookup(field='quantity_l', title='Кол-во L', mode=DisplayMode.markdown),
                    DisplayLookup(field='sending_method', title='Метод отправки', mode=DisplayMode.markdown),
                    DisplayLookup(field='status', title='Статус'),
                    # DisplayLookup(field='fish', title='ID FIS`'),
                    # DisplayLookup(field='cheque', title='ID Чека'),
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


@app.get('/api/article_info', response_model=FastUI, response_model_exclude_none=True)
async def articles_view(page: int = 1) -> list[AnyComponent]:
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
        title='Список артикулов находящихся в пути',
    )


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
                                      vendor_internal_article=order.vendor_internal_article, quantity_s=order.quantity_s,
                                      quantity_m=order.quantity_m, quantity_l=order.quantity_l,
                                      color=order.color, shop_name=order.shop_name, sending_method=order.sending_method,
                                      order_image=order.order_image, status=order.status,
                                      flag=order.flag)
                orders_full.append(order_object)
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
