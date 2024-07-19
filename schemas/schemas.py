from typing import Optional

import pydantic
from pydantic import BaseModel, Field, validator, field_validator


class SOrderAdd(BaseModel):
    create_date: str
    change_date: str
    internal_article: str
    vendor_internal_article: Optional[str] = 'Не заполнено'
    quantity_s: int
    quantity_m: int
    quantity_l: int
    color: str
    shop_name: str
    sending_method: str
    order_image: Optional[str] = None
    status: Optional[str] = 'Заказ не готов'
    flag: Optional[bool] = False


class SShipmentAdd(BaseModel):
    order_id: int
    create_date: str
    change_date: str
    quantity_s: int
    quantity_m: int
    quantity_l: int
    status: str
    sending_method: str
    sack_number: str
    sending_method: str
    fish: str
    cheque: str
    document_1_id: str
    document_2_id: str
    image_1_id: str
    image_2_id: str


class SChequeAdd(BaseModel):
    shipment_id: int
    order_id: int
    date: str
    create_date: str
    shop_name: str
    cheque_number: int
    vendor_internal_article: str
    price: int
    cheque_image_id: str
    cheque_status: str
    payment_image: str


class SFishAdd(BaseModel):
    shipment_id: int
    order_id: int
    fish_number: int
    fish_date: str
    weight: int
    sack_count: int
    sending_method: str
    fish_image_id: str


class SCardAdd(BaseModel):
    article: str
    image_id: str
    color: str
    shop_name: str
    vendor_internal_article: str


class SOrder(SOrderAdd):
    id: int


class SShipment(SShipmentAdd):
    id: int


class SCheque(SChequeAdd):
    id: int


class SFish(SFishAdd):
    id: int


class SCard(SCardAdd):
    id: int


class SOrderId(BaseModel):
    ok: bool = True
    order_id: int


class SShipmentId(BaseModel):
    ok: bool = True
    shipment_id: int


class SChequeId(BaseModel):
    ok: bool = True
    cheque_id: int


class SFishId(BaseModel):
    ok: bool = True
    fish_id: int


class SCardId(BaseModel):
    ok: bool = True
    fish_id: int

class BasePaymentIncome(BaseModel):
    id: int
    name: str
    code: int
    amount: float
    date: str
class SODDSpayment(BasePaymentIncome):
    pass

class SODDSincome(BasePaymentIncome):
    pass

class SODDSFilterForm(pydantic.BaseModel):
    date: str = Field(json_schema_extra={'search_url': '/odds/search', 'placeholder': 'Фильтрация по периоду...'})

class ReportODDSRequest(BaseModel):
    period: str = Field(
        ...,
        pattern=r'^\d{4}-(0?[1-9]|1[0-2])$',
        title='Период',
        description="Формат должен быть YYYY-MM, где YYYY - год, а MM - месяц в диапазоне от 01 до 12 или от 1 до 12"
    )
