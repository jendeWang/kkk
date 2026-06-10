from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class DataTypeEnum(str, enum.Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    ENUM = "enum"
    JSON = "json"


class AccessTypeEnum(str, enum.Enum):
    R = "r"
    W = "w"
    RW = "rw"


class DeviceStatusEnum(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class CommandStatusEnum(str, enum.Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"


class AlertTypeEnum(str, enum.Enum):
    THRESHOLD = "threshold"
    DEVICE_STATUS = "device_status"


class SeverityEnum(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatusEnum(str, enum.Enum):
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class PermissionLevelEnum(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class QualityEnum(str, enum.Enum):
    GOOD = "good"
    BAD = "bad"
    UNCERTAIN = "uncertain"


# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    products = relationship("Product", back_populates="owner")
    devices = relationship("Device", back_populates="owner")
    alert_rules = relationship("AlertRule", back_populates="owner")
    api_keys = relationship("APIKey", back_populates="owner")


# Product Model
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="products")
    properties = relationship("ProductProperty", back_populates="product", cascade="all, delete-orphan")
    services = relationship("ProductService", back_populates="product", cascade="all, delete-orphan")
    events = relationship("ProductEvent", back_populates="product", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="product")


class ProductProperty(Base):
    __tablename__ = "product_properties"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    identifier = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    data_type = Column(SQLEnum(DataTypeEnum), nullable=False)
    access_type = Column(SQLEnum(AccessTypeEnum), nullable=False)
    unit = Column(String(20), nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    default_value = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    product = relationship("Product", back_populates="properties")


class ProductService(Base):
    __tablename__ = "product_services"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    identifier = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    input_params = Column(JSON, nullable=True)
    output_params = Column(JSON, nullable=True)

    product = relationship("Product", back_populates="services")


class ProductEvent(Base):
    __tablename__ = "product_events"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    identifier = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    output_params = Column(JSON, nullable=True)

    product = relationship("Product", back_populates="events")


# Device Model
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_key = Column(String(32), unique=True, index=True, nullable=False)
    device_secret = Column(String(64), nullable=False)
    device_name = Column(String(100), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    status = Column(SQLEnum(DeviceStatusEnum), default=DeviceStatusEnum.OFFLINE)
    last_seen = Column(DateTime, nullable=True)
    status_changed_at = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    extra = Column(JSON, nullable=True)

    product = relationship("Product", back_populates="devices")
    owner = relationship("User", back_populates="devices")
    telemetry = relationship("Telemetry", back_populates="device", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="device", cascade="all, delete-orphan")
    event_records = relationship("DeviceEventRecord", back_populates="device", cascade="all, delete-orphan")
    alert_events = relationship("AlertEvent", back_populates="device")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    property_identifier = Column(String(100), nullable=False)
    value = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    quality = Column(String(20), nullable=True)

    device = relationship("Device", back_populates="telemetry")


class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(String(64), unique=True, index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    service_identifier = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=False)
    status = Column(SQLEnum(CommandStatusEnum), default=CommandStatusEnum.PENDING)
    issued_at = Column(DateTime, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    device = relationship("Device", back_populates="commands")


class DeviceEventRecord(Base):
    __tablename__ = "device_event_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    event_identifier = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False)

    device = relationship("Device", back_populates="event_records")


# Alert Models
class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    alert_type = Column(SQLEnum(AlertTypeEnum), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    property_identifier = Column(String(100), nullable=True)
    operator = Column(String(10), nullable=True)
    threshold_value = Column(String, nullable=True)
    severity = Column(SQLEnum(SeverityEnum), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    cooldown_seconds = Column(Integer, nullable=True)
    silent_from_hour = Column(Integer, nullable=True)
    silent_to_hour = Column(Integer, nullable=True)
    enabled = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="alert_rules")
    device = relationship("Device")
    alert_events = relationship("AlertEvent", back_populates="rule")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    message = Column(String(500), nullable=False)
    severity = Column(SQLEnum(SeverityEnum), nullable=False)
    current_value = Column(String, nullable=True)
    threshold_value = Column(String, nullable=True)
    status = Column(SQLEnum(AlertStatusEnum), default=AlertStatusEnum.TRIGGERED)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    rule = relationship("AlertRule", back_populates="alert_events")
    device = relationship("Device", back_populates="alert_events")


# API Key Model
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    permission_level = Column(SQLEnum(PermissionLevelEnum), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    owner = relationship("User", back_populates="api_keys")
