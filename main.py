from pathlib import Path

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from fastui.components.display import DisplayLookup, DisplayMode
from fastui.forms import fastui_form
from openpyxl.worksheet import page
from starlette.responses import HTMLResponse, FileResponse

from database import async_main, delete_tables, async_session_ODDS_
from routers.router import order_router, shipment_router, cheque_router, fish_router, ODDS_router, generate_report_ODDS
from typing import Annotated, Sequence, Union

from fastapi import APIRouter, Depends

from repository import OrderRepository, ShipmentRepository, ChequeRepository, FishRepository, ODDSRepository
from schemas.schemas import (SOrderAdd, SOrder, SOrderId, SShipment, SShipmentAdd, SShipmentId, SChequeAdd, SCheque,
                             SChequeId,
                             SFish, SFishAdd, SFishId, ReportODDSRequest, SODDSpayment, SODDSincome, BasePaymentIncome)

from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.events import GoToEvent, PageEvent, BackEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
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
                c.Link(
                    components=[c.Text(text='Отчет ОДДС')],
                    on_click=GoToEvent(url='/odds'),
                    active='startswith:/odss',
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

def ODDS_tabs() -> list[AnyComponent]:
    return [
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Платежи')],
                    on_click=GoToEvent(url='/odds/payments'),
                    active='startswith:/odds/payments',
                ),
                c.Link(
                    components=[c.Text(text='Поступления')],
                    on_click=GoToEvent(url='/odds/incomes'),
                    active='startswith:/orders/incomes',
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

@app.get("/api/odds", response_model=FastUI, response_model_exclude_none=True)
async def odds_payments_and_incomes(page: int = 1) -> list[AnyComponent]:
    payments = await ODDSRepository.all_payments()
    incomes = await ODDSRepository.all_incomes()
    payments_and_incomes_full = []
    page_size = 12
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



    return main_page(
        *ODDS_tabs(),
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

@app.get('api/odds/payments', response_model=FastUI, response_model_exclude_none=True)
async def odds_payments_view(page: int = 1) -> list[AnyComponent]:
    payments = await ODDSRepository.all_payments()
    payments_full = []
    page_size = 9
    for payment in payments:
        payment_obj = SODDSpayment(id=payment.id,
                                   name=payment.name,
                                   code=payment.code,
                                   amount=payment.amount,
                                   date=payment.date)
        payments_full.append(payment_obj)
    return main_page(
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
        title='Отчет ОДДС',
    )
@app.get('api/odds/incomes', response_model=FastUI, response_model_exclude_none=True)
async def odds_incomes_view(page: int = 1) -> list[AnyComponent]:
    incomes = await ODDSRepository.all_incomes()
    incomes_full = []
    page_size = 3
    for income in incomes:
        income_object = SODDSincome(
            id=income.id,
            name=income.name,
            code=income.code,
            amount=income.amount,
            date=income.date
        )
        incomes_full.append(income_object)
    print(incomes_full)
    return main_page(
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
