from typing import Optional

from pydantic import BaseModel


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


class SOrder(SOrderAdd):
    id: int


class SOrderId(BaseModel):
    ok: bool = True
    task_id: int
