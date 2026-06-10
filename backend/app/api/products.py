from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import uuid
import random
import string

from .deps import get_current_active_user, get_db
from ..models.models import (
    User, Product, ProductProperty, ProductService, ProductEvent, Device,
    PropertyDataType, PropertyAccessType,
)
from ..schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductDetailResponse,
    ProductPropertyCreate, ProductPropertyUpdate, ProductPropertyResponse,
    ProductServiceCreate, ProductServiceUpdate, ProductServiceResponse,
    ProductEventCreate, ProductEventUpdate, ProductEventResponse,
)

router = APIRouter(prefix="/products", tags=["产品管理"])


def _generate_product_key(length: int = 16) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品列表"""
    result = await db.execute(
        select(Product)
        .where(Product.owner_id == current_user.id)
        .order_by(desc(Product.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()


@router.get("/{product_key}", response_model=ProductDetailResponse)
async def get_product(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品详情（包含属性、服务、事件列表和设备数量）"""
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.properties),
            selectinload(Product.services),
            selectinload(Product.events),
        )
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 统计设备数量
    count_result = await db.execute(
        select(func.count(Device.id)).where(Device.product_id == product.id)
    )
    device_count = count_result.scalar() or 0

    response = ProductDetailResponse(
        id=product.id,
        product_key=product.product_key,
        name=product.name,
        category=product.category,
        model=product.model,
        manufacturer=product.manufacturer,
        description=product.description,
        owner_id=product.owner_id,
        created_at=product.created_at,
        properties=product.properties,
        services=product.services,
        events=product.events,
        device_count=device_count,
    )
    return response


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新产品"""
    new_product = Product(
        product_key=_generate_product_key(),
        name=product_data.name,
        category=product_data.category,
        model=product_data.model,
        manufacturer=product_data.manufacturer,
        description=product_data.description,
        owner_id=current_user.id,
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.put("/{product_key}", response_model=ProductResponse)
async def update_product(
    product_key: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新产品信息"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product_data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_key}")
async def delete_product(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除产品（及其下的属性、服务、事件、设备）"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.devices))
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.devices:
        raise HTTPException(status_code=400, detail="Cannot delete product with devices")

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}


# ========== Product Properties ==========

@router.get("/{product_key}/properties", response_model=List[ProductPropertyResponse])
async def list_product_properties(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品属性列表"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.properties))
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.properties


@router.post("/{product_key}/properties", response_model=ProductPropertyResponse)
async def create_product_property(
    product_key: str,
    prop_data: ProductPropertyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """添加产品属性（identifier 在产品内唯一）"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.properties))
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if any(p.identifier == prop_data.identifier for p in product.properties):
        raise HTTPException(status_code=400, detail=f"Property identifier '{prop_data.identifier}' already exists")

    new_prop = ProductProperty(
        product_id=product.id,
        identifier=prop_data.identifier,
        name=prop_data.name,
        data_type=PropertyDataType(prop_data.data_type),
        access_type=PropertyAccessType(prop_data.access_type),
        unit=prop_data.unit,
        min_value=prop_data.min_value,
        max_value=prop_data.max_value,
        default_value=prop_data.default_value,
        description=prop_data.description,
    )
    db.add(new_prop)
    await db.commit()
    await db.refresh(new_prop)
    return new_prop


@router.put("/{product_key}/properties/{property_id}", response_model=ProductPropertyResponse)
async def update_product_property(
    product_key: str,
    property_id: int,
    prop_data: ProductPropertyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新产品属性"""
    product_result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    prop_result = await db.execute(
        select(ProductProperty).where(
            ProductProperty.id == property_id,
            ProductProperty.product_id == product.id,
        )
    )
    prop = prop_result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if prop_data.identifier and prop_data.identifier != prop.identifier:
        check_result = await db.execute(
            select(ProductProperty).where(
                ProductProperty.product_id == product.id,
                ProductProperty.identifier == prop_data.identifier,
                ProductProperty.id != property_id,
            )
        )
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Property identifier '{prop_data.identifier}' already exists")

    for field, value in prop_data.model_dump(exclude_unset=True).items():
        if field == "data_type" and value is not None:
            value = PropertyDataType(value)
        elif field == "access_type" and value is not None:
            value = PropertyAccessType(value)
        setattr(prop, field, value)
    await db.commit()
    await db.refresh(prop)
    return prop


@router.delete("/{product_key}/properties/{property_id}")
async def delete_product_property(
    product_key: str,
    property_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除产品属性"""
    product_result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    prop_result = await db.execute(
        select(ProductProperty).where(
            ProductProperty.id == property_id,
            ProductProperty.product_id == product.id,
        )
    )
    prop = prop_result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    await db.delete(prop)
    await db.commit()
    return {"message": "Property deleted successfully"}


# ========== Product Services ==========

@router.get("/{product_key}/services", response_model=List[ProductServiceResponse])
async def list_product_services(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品服务列表"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.services))
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.services


@router.post("/{product_key}/services", response_model=ProductServiceResponse)
async def create_product_service(
    product_key: str,
    service_data: ProductServiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """添加产品服务"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.services))
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if any(s.identifier == service_data.identifier for s in product.services):
        raise HTTPException(status_code=400, detail=f"Service identifier '{service_data.identifier}' already exists")

    new_service = ProductService(
        product_id=product.id,
        identifier=service_data.identifier,
        name=service_data.name,
        description=service_data.description,
        input_params=service_data.input_params,
        output_params=service_data.output_params,
    )
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    return new_service


@router.put("/{product_key}/services/{service_id}", response_model=ProductServiceResponse)
async def update_product_service(
    product_key: str,
    service_id: int,
    service_data: ProductServiceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新产品服务"""
    product_result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    service_result = await db.execute(
        select(ProductService).where(
            ProductService.id == service_id,
            ProductService.product_id == product.id,
        )
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service_data.identifier and service_data.identifier != service.identifier:
        check_result = await db.execute(
            select(ProductService).where(
                ProductService.product_id == product.id,
                ProductService.identifier == service_data.identifier,
                ProductService.id != service_id,
            )
        )
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Service identifier '{service_data.identifier}' already exists")

    for field, value in service_data.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/{product_key}/services/{service_id}")
async def delete_product_service(
    product_key: str,
    service_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除产品服务"""
    product_result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    service_result = await db.execute(
        select(ProductService).where(
            ProductService.id == service_id,
            ProductService.product_id == product.id,
        )
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    await db.delete(service)
    await db.commit()
    return {"message": "Service deleted successfully"}


# ========== Product Events ==========

@router.get("/{product_key}/events", response_model=List[ProductEventResponse])
async def list_product_events(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品事件列表"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.events))
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.events


@router.post("/{product_key}/events", response_model=ProductEventResponse)
async def create_product_event(
    product_key: str,
    event_data: ProductEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """添加产品事件"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.events))
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if any(e.identifier == event_data.identifier for e in product.events):
        raise HTTPException(status_code=400, detail=f"Event identifier '{event_data.identifier}' already exists")

    new_event = ProductEvent(
        product_id=product.id,
        identifier=event_data.identifier,
        name=event_data.name,
        event_type=event_data.event_type,
        description=event_data.description,
        output_params=event_data.output_params,
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event


@router.put("/{product_key}/events/{event_id}", response_model=ProductEventResponse)
async def update_product_event(
    product_key: str,
    event_id: int,
    event_data: ProductEventUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新产品事件"""
    product_result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    event_result = await db.execute(
        select(ProductEvent).where(
            ProductEvent.id == event_id,
            ProductEvent.product_id == product.id,
        )
    )
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event_data.identifier and event_data.identifier != event.identifier:
        check_result = await db.execute(
            select(ProductEvent).where(
                ProductEvent.product_id == product.id,
                ProductEvent.identifier == event_data.identifier,
                ProductEvent.id != event_id,
            )
        )
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Event identifier '{event_data.identifier}' already exists")

    for field, value in event_data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/{product_key}/events/{event_id}")
async def delete_product_event(
    product_key: str,
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除产品事件"""
    product_result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    event_result = await db.execute(
        select(ProductEvent).where(
            ProductEvent.id == event_id,
            ProductEvent.product_id == product.id,
        )
    )
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted successfully"}
