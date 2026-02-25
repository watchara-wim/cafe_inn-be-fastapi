"""
Product Schemas

Pydantic models สำหรับ Product API
"""

from pydantic import BaseModel


class ProductResponse(BaseModel):
    """Response schema สำหรับ product"""
    product_id: int
    product_name: str
    price: int
    sweetness_options: list[str] | None = []
    milk_type_options: list[str] | None = []
    type_options: list[str] | None = []
    image: str | None = None

    class Config:
        from_attributes = True
