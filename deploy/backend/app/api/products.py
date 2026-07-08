from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
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
    TSLModel, TSLImportResponse,
)
from ..services.init_service import refresh_product_ui_specs

router = APIRouter(prefix="/products", tags=["产品管理"])


def _generate_product_key(length: int = 16) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


_ACCESS_TYPE_ALIASES = {
    "rw": "read_write",
    "wr": "read_write",
    "read_write": "read_write",
    "readwrite": "read_write",
    "w": "read_write",
    "write": "read_write",
    "r": "read_only",
    "ro": "read_only",
    "read_only": "read_only",
    "readonly": "read_only",
    "read": "read_only",
}


def _normalize_access_type(value: Optional[str]) -> Optional[str]:
    """将常见的 access_type 别名归一化为枚举值 (read_only / read_write)"""
    if value is None:
        return None
    return _ACCESS_TYPE_ALIASES.get(str(value).strip().lower(), value)


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
        access_type=PropertyAccessType(_normalize_access_type(prop_data.access_type)),
        unit=prop_data.unit,
        min_value=prop_data.min_value,
        max_value=prop_data.max_value,
        step=prop_data.step,
        enum_values=prop_data.enum_values,
        default_value=prop_data.default_value,
        required=prop_data.required,
        specs=prop_data.specs,
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


# ========== TSL 物模型导出/导入 ==========

@router.get("/{product_key}/tsl", response_model=TSLModel)
async def export_tsl(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """导出产品TSL物模型（标准JSON格式）"""
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

    properties = []
    for prop in product.properties:
        specs = {}
        if prop.min_value is not None:
            specs["min"] = _parse_value_by_type(prop.data_type, prop.min_value)
        if prop.max_value is not None:
            specs["max"] = _parse_value_by_type(prop.data_type, prop.max_value)
        if prop.step is not None:
            specs["step"] = _parse_value_by_type(prop.data_type, prop.step)
        if prop.unit:
            specs["unit"] = prop.unit
        if prop.enum_values:
            specs["enum"] = [_parse_value_by_type(prop.data_type, v) for v in prop.enum_values]

        properties.append({
            "identifier": prop.identifier,
            "name": prop.name,
            "dataType": prop.data_type.value if hasattr(prop.data_type, 'value') else prop.data_type,
            "accessType": prop.access_type.value if hasattr(prop.access_type, 'value') else prop.access_type,
            "required": prop.required or False,
            "specs": specs if specs else None,
            "description": prop.description,
        })

    services = []
    for svc in product.services:
        input_params = []
        output_params = []
        if isinstance(svc.input_params, list):
            for p in svc.input_params:
                input_params.append({
                    "identifier": p.get("identifier", ""),
                    "name": p.get("name", ""),
                    "dataType": p.get("dataType", "string"),
                    "specs": p.get("specs"),
                })
        if isinstance(svc.output_params, list):
            for p in svc.output_params:
                output_params.append({
                    "identifier": p.get("identifier", ""),
                    "name": p.get("name", ""),
                    "dataType": p.get("dataType", "string"),
                    "specs": p.get("specs"),
                })
        services.append({
            "identifier": svc.identifier,
            "name": svc.name,
            "description": svc.description,
            "inputParams": input_params,
            "outputParams": output_params,
        })

    events = []
    for evt in product.events:
        output_params = []
        if isinstance(evt.output_params, list):
            for p in evt.output_params:
                output_params.append({
                    "identifier": p.get("identifier", ""),
                    "name": p.get("name", ""),
                    "dataType": p.get("dataType", "string"),
                    "specs": p.get("specs"),
                })
        events.append({
            "identifier": evt.identifier,
            "name": evt.name,
            "eventType": evt.event_type or "info",
            "description": evt.description,
            "outputParams": output_params,
        })

    return TSLModel(
        version=product.tsl_version or "1.0",
        product_key=product.product_key,
        name=product.name,
        category=product.category,
        description=product.description,
        properties=properties,
        services=services,
        events=events,
    )


@router.get("/{product_key}/tsl/export")
async def export_tsl_file(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """导出产品TSL物模型为JSON文件下载"""
    tsl_data = await export_tsl(product_key, current_user, db)
    json_str = json.dumps(tsl_data.model_dump(), ensure_ascii=False, indent=2)
    json_bytes = json_str.encode('utf-8-sig')
    filename = f"{product_key}_tsl.json"
    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/tsl/import", response_model=TSLImportResponse)
async def import_tsl(
    tsl_data: TSLModel,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """通过TSL物模型创建产品（属性、服务、事件）"""
    product_key = tsl_data.product_key or _generate_product_key()

    existing = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Product '{product_key}' already exists")

    new_product = Product(
        product_key=product_key,
        name=tsl_data.name,
        category=tsl_data.category,
        description=tsl_data.description,
        tsl_version=tsl_data.version,
        owner_id=current_user.id,
    )
    db.add(new_product)
    await db.flush()

    for prop in tsl_data.properties:
        specs = prop.specs.model_dump() if prop.specs else {}
        min_val = str(specs.get("min")) if specs.get("min") is not None else None
        max_val = str(specs.get("max")) if specs.get("max") is not None else None
        step_val = str(specs.get("step")) if specs.get("step") is not None else None
        enum_vals = [str(v) for v in specs.get("enum", [])] if specs.get("enum") else None

        new_prop = ProductProperty(
            product_id=new_product.id,
            identifier=prop.identifier,
            name=prop.name,
            data_type=PropertyDataType(prop.dataType),
            access_type=PropertyAccessType(prop.accessType),
            unit=specs.get("unit"),
            min_value=min_val,
            max_value=max_val,
            step=step_val,
            enum_values=enum_vals,
            required=prop.required or False,
            specs=specs if specs else None,
            description=prop.description,
        )
        db.add(new_prop)

    for svc in tsl_data.services:
        input_params = [p.model_dump() for p in svc.inputParams] if svc.inputParams else []
        output_params = [p.model_dump() for p in svc.outputParams] if svc.outputParams else []

        new_svc = ProductService(
            product_id=new_product.id,
            identifier=svc.identifier,
            name=svc.name,
            description=svc.description,
            input_params=input_params,
            output_params=output_params,
        )
        db.add(new_svc)

    for evt in tsl_data.events:
        output_params = [p.model_dump() for p in evt.outputParams] if evt.outputParams else []

        new_evt = ProductEvent(
            product_id=new_product.id,
            identifier=evt.identifier,
            name=evt.name,
            event_type=evt.eventType,
            description=evt.description,
            output_params=output_params,
        )
        db.add(new_evt)

    await db.commit()
    await db.refresh(new_product)

    return TSLImportResponse(
        product_key=new_product.product_key,
        name=new_product.name,
        properties_count=len(tsl_data.properties),
        services_count=len(tsl_data.services),
        events_count=len(tsl_data.events),
    )


@router.get("/{product_key}/tsl/detail")
async def get_tsl_detail(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品TSL详情（属性含完整specs、服务、事件）"""
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

    properties = []
    for prop in product.properties:
        properties.append({
            "id": prop.id,
            "identifier": prop.identifier,
            "name": prop.name,
            "data_type": prop.data_type.value if hasattr(prop.data_type, 'value') else prop.data_type,
            "access_type": prop.access_type.value if hasattr(prop.access_type, 'value') else prop.access_type,
            "unit": prop.unit,
            "min_value": prop.min_value,
            "max_value": prop.max_value,
            "step": prop.step,
            "enum_values": prop.enum_values,
            "default_value": prop.default_value,
            "required": prop.required or False,
            "specs": prop.specs or {},
            "description": prop.description,
            "created_at": prop.created_at,
        })

    services = []
    for svc in product.services:
        services.append({
            "id": svc.id,
            "identifier": svc.identifier,
            "name": svc.name,
            "description": svc.description,
            "input_params": svc.input_params or [],
            "output_params": svc.output_params or [],
            "created_at": svc.created_at,
        })

    events = []
    for evt in product.events:
        events.append({
            "id": evt.id,
            "identifier": evt.identifier,
            "name": evt.name,
            "event_type": evt.event_type,
            "description": evt.description,
            "output_params": evt.output_params or [],
            "created_at": evt.created_at,
        })

    return {
        "properties": properties,
        "services": services,
        "events": events,
    }


@router.post("/{product_key}/refresh-ui-specs")
async def refresh_ui_specs(
    product_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """为产品属性补充UI配置（根据identifier匹配）"""
    result = await db.execute(
        select(Product).where(
            Product.product_key == product_key,
            Product.owner_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    updated_count = await refresh_product_ui_specs(db, product.id)

    return {
        "message": f"Updated {updated_count} properties",
        "updated_count": updated_count,
    }


# ========== Product Templates ==========

@router.get("/templates/list")
async def list_product_templates(
    current_user: User = Depends(get_current_active_user),
):
    """获取产品模板列表"""
    from ..services.template_service import list_templates
    return list_templates()


@router.post("/from-template/{template_id}")
async def create_product_from_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    custom_name: str | None = None,
    create_default_device: bool = True,
    create_alert_rules: bool = True,
    create_scenes: bool = True,
):
    """从模板创建产品（一键生成产品、属性、服务、事件、默认设备、告警规则、自动化场景）"""
    from ..services.template_service import create_product_from_template as create_from_tpl

    try:
        product = await create_from_tpl(
            db=db,
            current_user=current_user,
            template_id=template_id,
            custom_name=custom_name,
            create_default_device=create_default_device,
            create_alert_rules=create_alert_rules,
            create_scenes=create_scenes,
        )
        return {
            "product_key": product.product_key,
            "name": product.name,
            "properties_count": len(product.properties),
            "services_count": len(product.services),
            "events_count": len(product.events),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _parse_value_by_type(data_type, value_str):
    """根据数据类型解析值字符串"""
    if value_str is None:
        return None
    try:
        dt = data_type.value if hasattr(data_type, 'value') else data_type
        if dt == "int":
            return int(float(value_str))
        elif dt == "float":
            return float(value_str)
        elif dt == "bool":
            return value_str.lower() in ("true", "1", "yes")
        else:
            return value_str
    except (ValueError, TypeError):
        return value_str
