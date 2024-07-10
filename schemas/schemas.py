from typing import Optional

from pydantic import BaseModel


class SOrderAdd(BaseModel):
    create_date: Optional[str] = None
    change_date: Optional[str] = None
    internal_article: str
    vendor_internal_article: Optional[str] = '-'
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
    sack_number: Optional[str] = None
    sending_method: str
    fish: int
    cheque: int
    document_1_id: Optional[str] = None
    document_2_id: Optional[str] = None
    image_1_id: Optional[str] = None
    image_2_id: Optional[str] = None


class SChequeAdd(BaseModel):
    shipment_id: int
    order_id: int
    date: str
    create_date: str
    shop_name: str
    cheque_number: int
    vendor_internal_article: int
    price: int
    cheque_image_id: str
    cheque_status: Optional[str] = 'По чеку имеется отсрочка'
    payment_image: Optional[str] = None


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