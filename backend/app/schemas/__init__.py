from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# Auth schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Product schemas
class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    product_key: str
    owner_id: int

    class Config:
        from_attributes = True


class ProductDetailResponse(ProductResponse):
    properties: List["ProductPropertyResponse"] = []
    services: List["ProductServiceResponse"] = []
    events: List["ProductEventResponse"] = []


# Product Property schemas
class ProductPropertyBase(BaseModel):
    identifier: str
    name: str
    data_type: str
    access_type: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[str] = None
    description: Optional[str] = None


class ProductPropertyCreate(ProductPropertyBase):
    pass


class ProductPropertyResponse(ProductPropertyBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True


# Product Service schemas
class ProductServiceBase(BaseModel):
    identifier: str
    name: str
    description: Optional[str] = None
    input_params: Optional[Any] = None
    output_params: Optional[Any] = None


class ProductServiceCreate(ProductServiceBase):
    pass


class ProductServiceResponse(ProductServiceBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True


# Product Event schemas
class ProductEventBase(BaseModel):
    identifier: str
    name: str
    event_type: Optional[str] = None
    description: Optional[str] = None
    output_params: Optional[Any] = None


class ProductEventCreate(ProductEventBase):
    pass


class ProductEventResponse(ProductEventBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True


# Device schemas
class DeviceBase(BaseModel):
    device_name: str
    product_id: int
    extra: Optional[Any] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    extra: Optional[Any] = None


class DeviceResponse(BaseModel):
    id: int
    device_key: str
    device_name: str
    product_id: int
    status: str
    last_seen: Optional[datetime] = None
    owner_id: int
    extra: Optional[Any] = None

    class Config:
        from_attributes = True


class DeviceDetailResponse(DeviceResponse):
    product: ProductResponse


# Telemetry schemas
class TelemetryResponse(BaseModel):
    id: int
    device_id: int
    property_identifier: str
    value: str
    timestamp: datetime
    quality: Optional[str] = None

    class Config:
        from_attributes = True


# Command schemas
class CommandBase(BaseModel):
    device_id: int
    service_identifier: str
    parameters: Optional[Any] = None


class CommandCreate(CommandBase):
    pass


class CommandResponse(CommandBase):
    id: int
    command_id: str
    status: str
    issued_at: datetime
    executed_at: Optional[datetime] = None
    output_data: Optional[Any] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# Alert schemas
class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    alert_type: str
    device_id: Optional[int] = None
    property_identifier: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[str] = None
    severity: str
    duration_seconds: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    silent_from_hour: Optional[int] = None
    silent_to_hour: Optional[int] = None
    enabled: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    alert_type: Optional[str] = None
    device_id: Optional[int] = None
    property_identifier: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[str] = None
    severity: Optional[str] = None
    duration_seconds: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    silent_from_hour: Optional[int] = None
    silent_to_hour: Optional[int] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    owner_id: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertEventResponse(BaseModel):
    id: int
    rule_id: Optional[int]
    device_id: int
    message: str
    severity: str
    current_value: Optional[str] = None
    threshold_value: Optional[str] = None
    status: str
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertEventStatusUpdate(BaseModel):
    status: str


# API Key schemas
class APIKeyBase(BaseModel):
    name: str
    permission_level: str


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyResponse(APIKeyBase):
    id: int
    key: str
    owner_id: int
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True
