"""
Product Schemas

Pydantic models สำหรับ Product API
"""

from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    """Response schema สำหรับ product"""
    product_id: int
    product_name: str
    price: int
    sweetness_options: list[str] | None = []
    milk_type_options: list[str] | None = []
    type_options: list[str] | None = []
    image: str | None = None

    model_config = ConfigDict(from_attributes=True)
