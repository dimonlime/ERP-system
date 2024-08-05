from typing import Annotated

from fastapi import APIRouter, Depends
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.events import GoToEvent, BackEvent
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.forms import fastui_form
from starlette.responses import HTMLResponse

from repository import OrderRepository, ShipmentRepository, ChequeRepository, FishRepository
from schemas.schemas import SOrderAdd, SOrder, SOrderId, SShipment, SShipmentAdd, SShipmentId, SChequeAdd, SCheque, \
    SChequeId, SFish, SFishAdd, SFishId, SWarehouseMovementForm

order_router = APIRouter()
router = APIRouter()
shipment_router = APIRouter(
    prefix='/shipment',
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


@order_router.post('/orders/add')
async def add_order(order: Annotated[SOrderAdd, fastui_form(SOrderAdd)]):
    order_id = await OrderRepository.add_order(order)
    return {'ok': True, 'order_id': order_id}


@order_router.get('orders/get')
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

