from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.events import GoToEvent, BackEvent
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.forms import fastui_form
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse, FileResponse
from fastapi.responses import StreamingResponse

from ODDS.create_excel_ODDS import frame_report_ODDS
from repository import OrderRepository, ShipmentRepository, ChequeRepository, FishRepository
from schemas.schemas import SOrderAdd, SOrder, SOrderId, SShipment, SShipmentAdd, SShipmentId, SChequeAdd, SCheque, \
    SChequeId, SFish, SFishAdd, SFishId, ReportODDSRequest
from database import async_session_ODDS, async_session_ODDS_

order_router = APIRouter(
    prefix='/orders',
    tags=['Заказы'],
)

shipment_router = APIRouter(
    prefix='/shipments',
    tags=['Поставки'],
)

cheque_router = APIRouter(
    prefix='/cheques',
    tags=['Чеки'],
)

fish_router = APIRouter(
    prefix='/fishes',
    tags=['FIS`'],
)

ODDS_router = APIRouter(
    prefix='/odds',
    tags=['ОДДС'],
)



@order_router.post('')
async def add_order(order: Annotated[SOrderAdd, Depends()]) -> SOrderId:
    order_id = await OrderRepository.add_order(order)
    return {'ok': True, 'order_id': order_id}


@order_router.get('')
async def get_orders() -> list[SOrder]:
    orders = await OrderRepository.all_orders()
    return orders


@shipment_router.post('')
async def add_shipment(shipment: Annotated[SShipmentAdd, Depends()]) -> SShipmentId:
    shipment_id = await ShipmentRepository.add_shipment(shipment)
    return {'ok': True, 'shipment_id': shipment_id}


@shipment_router.get('')
async def get_shipments() -> list[SShipment]:
    shipments = await ShipmentRepository.all_shipments()
    return shipments


@cheque_router.post('')
async def add_cheque(cheque: Annotated[SChequeAdd, Depends()]) -> SChequeId:
    cheque_id = await ChequeRepository.add_cheque(cheque)
    return {'ok': True, 'cheque_id': cheque_id}


@cheque_router.get('')
async def get_cheques() -> list[SCheque]:
    cheques = await ChequeRepository.all_cheques()
    return cheques


@fish_router.post('')
async def add_fish(fish: Annotated[SFishAdd, Depends()]) -> SFishId:
    fish_id = await FishRepository.add_fish(fish)
    return {'ok': True, 'fish_id': fish_id}


@fish_router.get('')
async def get_fishes() -> list[SFish]:
    fishes = await FishRepository.all_fishes()
    return fishes

@ODDS_router.post('')
async def generate_report_ODDS(request: ReportODDSRequest):
    try:
        period = request.period
        print(request)
        excel_path = "ODDS/excel_files/report_ODDS.xlsx"
        await frame_report_ODDS(period, excel_path)

        # Возвращаем файл клиенту как потоковый ответ
        file_path = Path(excel_path)
        return FileResponse(file_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=file_path.name)

    except Exception as e:
        # Обработка ошибок, если они возникнут
        raise HTTPException(status_code=500, detail=str(e))


