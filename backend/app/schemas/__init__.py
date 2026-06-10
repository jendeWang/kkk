from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any, Dict, Union
from datetime import datetime
import enum as _enum


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
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    properties: List["ProductPropertyResponse"] = []
    services: List["ProductServiceResponse"] = []
    events: List["ProductEventResponse"] = []
    device_count: int = 0


class ProductPropertyBase(BaseModel):
    identifier: str
    name: str
    data_type: str
    access_type: str
    unit: Optional[str] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    enum_values: Optional[List[str]] = None
    default_value: Optional[str] = None
    description: Optional[str] = None

    @field_validator("data_type", "access_type", mode="before")
    @classmethod
    def _enum_to_str(cls, v):
        if isinstance(v, _enum.Enum):
            return v.value
        return v


class ProductPropertyCreate(ProductPropertyBase):
    pass


class ProductPropertyUpdate(BaseModel):
    identifier: Optional[str] = None
    name: Optional[str] = None
    data_type: Optional[str] = None
    access_type: Optional[str] = None
    unit: Optional[str] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    enum_values: Optional[List[str]] = None
    default_value: Optional[str] = None
    description: Optional[str] = None


class ProductPropertyResponse(ProductPropertyBase):
    id: int
    product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductServiceBase(BaseModel):
    identifier: str
    name: str
    description: Optional[str] = None
    input_params: Optional[Dict[str, Any]] = None
    output_params: Optional[Dict[str, Any]] = None


class ProductServiceCreate(ProductServiceBase):
    pass


class ProductServiceUpdate(BaseModel):
    identifier: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    input_params: Optional[Dict[str, Any]] = None
    output_params: Optional[Dict[str, Any]] = None


class ProductServiceResponse(ProductServiceBase):
    id: int
    product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductEventBase(BaseModel):
    identifier: str
    name: str
    event_type: Optional[str] = None
    description: Optional[str] = None
    output_params: Optional[Dict[str, Any]] = None


class ProductEventCreate(ProductEventBase):
    pass


class ProductEventUpdate(BaseModel):
    identifier: Optional[str] = None
    name: Optional[str] = None
    event_type: Optional[str] = None
    description: Optional[str] = None
    output_params: Optional[Dict[str, Any]] = None


class ProductEventResponse(ProductEventBase):
    id: int
    product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceBase(BaseModel):
    device_name: str
    product_id: int
    extra: Optional[Dict[str, Any]] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class DeviceResponse(BaseModel):
    id: int
    device_key: str
    device_name: str
    product_id: int
    status: str
    last_seen: Optional[datetime] = None
    owner_id: int
    extra: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status", mode="before")
    @classmethod
    def _enum_status_to_str(cls, v):
        if isinstance(v, _enum.Enum):
            return v.value
        return v


class PropertyWithValueResponse(BaseModel):
    identifier: str
    name: str
    data_type: str
    unit: Optional[str] = None
    current_value: Optional[str] = None
    last_updated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("data_type", mode="before")
    @classmethod
    def _enum_dt_to_str(cls, v):
        if isinstance(v, _enum.Enum):
            return v.value
        return v


class DeviceDetailResponse(BaseModel):
    id: int
    device_key: str
    device_name: str
    product_id: int
    product_name: str
    status: str
    last_seen: Optional[datetime] = None
    owner_id: int
    extra: Optional[Dict[str, Any]] = None
    created_at: datetime
    properties: List[PropertyWithValueResponse] = []
    recent_commands: List["CommandResponse"] = []
    recent_events: List["DeviceEventRecordResponse"] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status", mode="before")
    @classmethod
    def _enum_status_to_str(cls, v):
        if isinstance(v, _enum.Enum):
            return v.value
        return v


class TelemetryResponse(BaseModel):
    id: int
    device_id: int
    property_identifier: str
    value: str
    timestamp: datetime
    quality: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CommandBase(BaseModel):
    device_id: int
    service_identifier: str
    input_params: Optional[Dict[str, Any]] = None


class CommandCreate(CommandBase):
    pass


class CommandSendRequest(BaseModel):
    service_identifier: str
    input_params: Optional[Dict[str, Any]] = None


class CommandResponse(BaseModel):
    id: int
    command_id: str
    device_id: int
    service_identifier: str
    input_params: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    owner_id: int
    created_at: datetime
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status", mode="before")
    @classmethod
    def _enum_status_to_str(cls, v):
        if isinstance(v, _enum.Enum):
            return v.value
        return v


class DeviceEventRecordResponse(BaseModel):
    id: int
    device_id: int
    event_identifier: str
    event_data: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    alert_type: str
    product_id: Optional[int] = None
    device_id: Optional[int] = None
    property_identifier: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[str] = None
    duration_seconds: Optional[int] = None
    delay_seconds: Optional[int] = None
    severity: str
    cooldown_seconds: Optional[int] = None
    silent_from_hour: Optional[int] = None
    silent_to_hour: Optional[int] = None
    notification_config: Optional[Dict[str, Any]] = None
    enabled: bool = True

    @field_validator("alert_type", "severity", "operator", mode="before")
    @classmethod
    def _enum_to_str(cls, v):
        if isinstance(v, _enum.Enum):
            return v.value
        return v


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    alert_type: Optional[str] = None
    product_id: Optional[int] = None
    device_id: Optional[int] = None
    property_identifier: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[str] = None
    duration_seconds: Optional[int] = None
    delay_seconds: Optional[int] = None
    severity: Optional[str] = None
    cooldown_seconds: Optional[int] = None
    silent_from_hour: Optional[int] = None
    silent_to_hour: Optional[int] = None
    notification_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    owner_id: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertEventResponse(BaseModel):
    id: int
    rule_id: Optional[int] = None
    product_id: Optional[int] = None
    device_id: int
    property_identifier: Optional[str] = None
    message: str
    severity: str
    current_value: Optional[str] = None
    threshold_value: Optional[str] = None
    operator: Optional[str] = None
    status: str
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("severity", "status", "operator", mode="before")
    @classmethod
    def _enum_to_str(cls, v):
        if isinstance(v, _enum.Enum):
            return v.value
        return v


class AlertEventStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


class APIKeyBase(BaseModel):
    name: str
    permissions: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    user_id: int
    permissions: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


ProductDetailResponse.model_rebuild()
DeviceDetailResponse.model_rebuild()
