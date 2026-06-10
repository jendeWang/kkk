from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from .deps import get_current_active_user
from ..database import get_db
from ..models.models import User, Product, ProductProperty, ProductService, ProductEvent
from ..schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductDetailResponse,
    ProductPropertyCreate, ProductPropertyResponse,
    ProductServiceCreate, ProductServiceResponse,
    ProductEventCreate, ProductEventResponse
)

router = APIRouter(prefix="/products", tags=["产品管理"])


def generate_product_key():
    """生成产品密钥"""
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))


@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建产品"""
    product_key = generate_product_key()
    db_product = Product(
        product_key=product_key,
        name=product.name,
        category=product.category,
        model=product.model,
        manufacturer=product.manufacturer,
        description=product.description,
        owner_id=current_user.id
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取产品列表"""
    result = await db.execute(
        select(Product).where(Product.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{product_key}", response_model=ProductDetailResponse)
async def get_product(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取产品详情"""
    result = await db.execute(
        select(Product)
        .where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
        .options(
            selectinload(Product.properties),
            selectinload(Product.services),
            selectinload(Product.events)
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_key}", response_model=ProductResponse)
async def update_product(
    product_key: str,
    product: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新产品"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)

    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_key}")
async def delete_product(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除产品"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}


# Property endpoints
@router.post("/{product_key}/properties", response_model=ProductPropertyResponse)
async def create_property(
    product_key: str,
    prop: ProductPropertyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建属性"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_prop = ProductProperty(
        product_id=product.id,
        identifier=prop.identifier,
        name=prop.name,
        data_type=prop.data_type,
        access_type=prop.access_type,
        unit=prop.unit,
        min_value=prop.min_value,
        max_value=prop.max_value,
        default_value=prop.default_value,
        description=prop.description
    )
    db.add(db_prop)
    await db.commit()
    await db.refresh(db_prop)
    return db_prop


@router.get("/{product_key}/properties", response_model=List[ProductPropertyResponse])
async def list_properties(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取属性列表"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    prop_result = await db.execute(
        select(ProductProperty).where(ProductProperty.product_id == product.id)
    )
    return prop_result.scalars().all()


@router.put("/{product_key}/properties/{identifier}", response_model=ProductPropertyResponse)
async def update_property(
    product_key: str,
    identifier: str,
    prop: ProductPropertyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新属性"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    prop_result = await db.execute(
        select(ProductProperty).where(
            ProductProperty.product_id == product.id,
            ProductProperty.identifier == identifier
        )
    )
    db_prop = prop_result.scalar_one_or_none()
    if not db_prop:
        raise HTTPException(status_code=404, detail="Property not found")

    for key, value in prop.model_dump(exclude_unset=True).items():
        setattr(db_prop, key, value)

    await db.commit()
    await db.refresh(db_prop)
    return db_prop


@router.delete("/{product_key}/properties/{identifier}")
async def delete_property(
    product_key: str,
    identifier: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除属性"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    prop_result = await db.execute(
        select(ProductProperty).where(
            ProductProperty.product_id == product.id,
            ProductProperty.identifier == identifier
        )
    )
    prop = prop_result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    await db.delete(prop)
    await db.commit()
    return {"message": "Property deleted successfully"}


# Service endpoints
@router.post("/{product_key}/services", response_model=ProductServiceResponse)
async def create_service(
    product_key: str,
    service: ProductServiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建服务"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_service = ProductService(
        product_id=product.id,
        identifier=service.identifier,
        name=service.name,
        description=service.description,
        input_params=service.input_params,
        output_params=service.output_params
    )
    db.add(db_service)
    await db.commit()
    await db.refresh(db_service)
    return db_service


@router.get("/{product_key}/services", response_model=List[ProductServiceResponse])
async def list_services(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务列表"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    svc_result = await db.execute(
        select(ProductService).where(ProductService.product_id == product.id)
    )
    return svc_result.scalars().all()


@router.put("/{product_key}/services/{identifier}", response_model=ProductServiceResponse)
async def update_service(
    product_key: str,
    identifier: str,
    service: ProductServiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新服务"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    svc_result = await db.execute(
        select(ProductService).where(
            ProductService.product_id == product.id,
            ProductService.identifier == identifier
        )
    )
    db_service = svc_result.scalar_one_or_none()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")

    for key, value in service.model_dump(exclude_unset=True).items():
        setattr(db_service, key, value)

    await db.commit()
    await db.refresh(db_service)
    return db_service


@router.delete("/{product_key}/services/{identifier}")
async def delete_service(
    product_key: str,
    identifier: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除服务"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    svc_result = await db.execute(
        select(ProductService).where(
            ProductService.product_id == product.id,
            ProductService.identifier == identifier
        )
    )
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    await db.delete(service)
    await db.commit()
    return {"message": "Service deleted successfully"}


# Event endpoints
@router.post("/{product_key}/events", response_model=ProductEventResponse)
async def create_event(
    product_key: str,
    event: ProductEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建事件"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_event = ProductEvent(
        product_id=product.id,
        identifier=event.identifier,
        name=event.name,
        event_type=event.event_type,
        description=event.description,
        output_params=event.output_params
    )
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event


@router.get("/{product_key}/events", response_model=List[ProductEventResponse])
async def list_events(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取事件列表"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    evt_result = await db.execute(
        select(ProductEvent).where(ProductEvent.product_id == product.id)
    )
    return evt_result.scalars().all()


@router.put("/{product_key}/events/{identifier}", response_model=ProductEventResponse)
async def update_event(
    product_key: str,
    identifier: str,
    event: ProductEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新事件"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    evt_result = await db.execute(
        select(ProductEvent).where(
            ProductEvent.product_id == product.id,
            ProductEvent.identifier == identifier
        )
    )
    db_event = evt_result.scalar_one_or_none()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    for key, value in event.model_dump(exclude_unset=True).items():
        setattr(db_event, key, value)

    await db.commit()
    await db.refresh(db_event)
    return db_event


@router.delete("/{product_key}/events/{identifier}")
async def delete_event(
    product_key: str,
    identifier: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除事件"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    evt_result = await db.execute(
        select(ProductEvent).where(
            ProductEvent.product_id == product.id,
            ProductEvent.identifier == identifier
        )
    )
    event = evt_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted successfully"}
