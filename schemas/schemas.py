import enum
from typing import Optional

from pydantic import BaseModel, Field


class SOrderAdd(BaseModel):
    create_date: Optional[str] = None
    change_date: Optional[str] = None
    internal_article: str
    vendor_internal_article: Optional[str] = '-'
    quantity_xs: int
    quantity_s: int
    quantity_m: int
    quantity_l: int
    color: str
    shop_name: str
    sending_method: str
    order_image: Optional[str] = None
    status: Optional[str] = 'Заказ не готов'
    flag: Optional[bool] = False


class ArticleEnum(str, enum.Enum):
    article1 = '51920232'
    article2 = '51920233'
    article3 = '51920231'
    article4 = 'TR792KTD1PL2000'
    article5 = 'TR792KTD1PB1700'
    article6 = 'TR792FKD1CPB12226'
    article7 = 'TR792KTD1PB1603'
    article8 = 'TR792KTD1PB24A4149'
    article9 = 'TR792KTD1PB5002'
    article10 = 'TR792KTD3PG1603'
    article11 = 'TR792KTD2PBR1603'
    article12 = 'TR792KTD1PB1701'
    article13 = 'TR792KTD2PGR1701'


class WarehouseEnum(str, enum.Enum):
    warehouse1 = 'Склад логистов'
    warehouse2 = 'Склад фуллфилмент'
    warehouse3 = 'Склад wildberries'
    warehouse4 = 'Склад ozon'
    warehouse5 = 'Склад yandex'



class SendingMethod(str, enum.Enum):
    T1 = 'T1'
    T2 = 'T2'
    Avia = 'Avia'


class SWarehouseMovementForm(BaseModel):
    start: WarehouseEnum = Field(title='Выберите склад с которого отправлять')
    destination: WarehouseEnum = Field(title='Выберите склад куда отправлять')
    quantity_xs: int = Field(title='Кол-во XS')
    quantity_s: int = Field(title='Кол-во S')
    quantity_m: int = Field(title='Кол-во M')
    quantity_l: int = Field(title='Кол-во L')
    comment: str = Field(title='Добавьте комментарий')


class SOrderAddForm(BaseModel):
    internal_article: ArticleEnum = Field(title='Выберите артикул')
    quantity_xs: int
    quantity_s: int = Field(title='Кол-во S')
    quantity_m: int = Field(title='Кол-во M')
    quantity_l: int = Field(title='Кол-во L')
    sending_method: SendingMethod = Field(title='Выберите метод отправки')


class SShipmentAdd(BaseModel):
    order_id: int
    create_date: str
    change_date: str
    quantity_xs: int
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


class SWarehouse(BaseModel):
    article: str
    quantity_xs: int
    quantity_s: int
    quantity_m: int
    quantity_l: int


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