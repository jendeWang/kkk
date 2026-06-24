from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import (
    User, Product, ProductProperty, ProductService, ProductEvent,
    PropertyDataType, PropertyAccessType,
)
from ..security.auth import get_password_hash
from ..config import settings


async def init_default_user(db: AsyncSession):
    """创建默认管理员用户"""
    result = await db.execute(select(User).where(User.username == "admin"))
    existing = result.scalar_one_or_none()
    if not existing:
        admin = User(
            username="admin",
            email="admin@iot.local",
            full_name="IoT Platform Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        await db.commit()
        print("[Init] Default admin user created: admin / admin123")
    else:
        print("[Init] Admin user already exists")


async def init_greenhouse_product(db: AsyncSession):
    """创建智慧大棚预置产品（4传感器+3执行器物模型）"""
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if not admin:
        return

    product_result = await db.execute(
        select(Product).where(
            Product.product_key == "smart_greenhouse",
            Product.owner_id == admin.id,
        )
    )
    existing = product_result.scalar_one_or_none()
    if existing:
        print("[Init] Smart Greenhouse product already exists")
        return

    product = Product(
        product_key="smart_greenhouse",
        name="智慧大棚",
        category="农业",
        model="GH-100",
        manufacturer="IoT Platform",
        description="智慧大棚标准物模型，包含温湿度、光照、土壤等传感器及通风、补光、灌溉等执行器",
        tsl_version="1.0",
        owner_id=admin.id,
    )
    db.add(product)
    await db.flush()

    properties = [
        {"identifier": "temperature", "name": "空气温度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "℃",
         "min_value": "-40", "max_value": "85", "step": "0.1", "required": True,
         "specs": {"min": -40, "max": 85, "step": 0.1, "unit": "℃"}},
        {"identifier": "humidity", "name": "空气湿度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "%RH",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {"min": 0, "max": 100, "step": 0.1, "unit": "%RH"}},
        {"identifier": "light_intensity", "name": "光照强度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "lux",
         "min_value": "0", "max_value": "100000", "step": "1", "required": True,
         "specs": {"min": 0, "max": 100000, "step": 1, "unit": "lux"}},
        {"identifier": "soil_moisture", "name": "土壤湿度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "%",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {"min": 0, "max": 100, "step": 0.1, "unit": "%"}},
        {"identifier": "co2", "name": "CO₂浓度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "ppm",
         "min_value": "0", "max_value": "5000", "step": "1", "required": False,
         "specs": {"min": 0, "max": 5000, "step": 1, "unit": "ppm"}},
        {"identifier": "soil_temperature", "name": "土壤温度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "℃",
         "min_value": "-20", "max_value": "60", "step": "0.1", "required": False,
         "specs": {"min": -20, "max": 60, "step": 0.1, "unit": "℃"}},
        {"identifier": "fan_status", "name": "通风扇状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {}},
        {"identifier": "light_status", "name": "补光灯状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {}},
        {"identifier": "pump_status", "name": "灌溉水泵状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {}},
        {"identifier": "brightness", "name": "补光灯亮度", "data_type": PropertyDataType.INT,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "%",
         "min_value": "0", "max_value": "100", "step": "1", "required": False,
         "specs": {"min": 0, "max": 100, "step": 1, "unit": "%"}},
        {"identifier": "work_mode", "name": "工作模式", "data_type": PropertyDataType.ENUM,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "enum_values": ["manual", "auto"], "default_value": "manual",
         "required": False, "specs": {"enum": ["manual", "auto"]}},
    ]

    for prop in properties:
        db.add(ProductProperty(product_id=product.id, **prop))

    services = [
        {"identifier": "set_fan", "name": "设置通风扇", "description": "开启或关闭通风扇",
         "input_params": [{"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_light", "name": "设置补光灯", "description": "控制补光灯开关和亮度",
         "input_params": [
             {"identifier": "status", "name": "开关状态", "dataType": "bool", "specs": {}},
             {"identifier": "brightness", "name": "亮度", "dataType": "int", "specs": {"min": 0, "max": 100, "unit": "%"}},
         ],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_pump", "name": "设置灌溉泵", "description": "控制灌溉水泵，可设置运行时长",
         "input_params": [
             {"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}},
             {"identifier": "duration", "name": "持续时间", "dataType": "int", "specs": {"min": 0, "unit": "秒"}},
         ],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_mode", "name": "设置工作模式", "description": "切换手动/自动模式",
         "input_params": [{"identifier": "mode", "name": "模式", "dataType": "enum", "specs": {"enum": ["manual", "auto"]}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "raw_command", "name": "自定义命令", "description": "发送自定义JSON命令",
         "input_params": [{"identifier": "data", "name": "命令数据", "dataType": "string", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "响应数据", "dataType": "string", "specs": {}}]},
    ]

    for svc in services:
        db.add(ProductService(product_id=product.id, **svc))

    events = [
        {"identifier": "water_shortage", "name": "缺水告警", "event_type": "alert",
         "description": "土壤湿度过低触发缺水告警",
         "output_params": [
             {"identifier": "current_moisture", "name": "当前湿度", "dataType": "float", "specs": {"unit": "%"}},
             {"identifier": "threshold", "name": "阈值", "dataType": "float", "specs": {"unit": "%"}},
         ]},
        {"identifier": "sensor_error", "name": "传感器故障", "event_type": "error",
         "description": "传感器数据异常或离线",
         "output_params": [
             {"identifier": "sensor", "name": "传感器标识", "dataType": "string", "specs": {}},
             {"identifier": "error_code", "name": "错误码", "dataType": "int", "specs": {}},
         ]},
        {"identifier": "task_complete", "name": "任务完成", "event_type": "info",
         "description": "自动化任务执行完成",
         "output_params": [
             {"identifier": "task_name", "name": "任务名称", "dataType": "string", "specs": {}},
             {"identifier": "success", "name": "是否成功", "dataType": "bool", "specs": {}},
         ]},
    ]

    for evt in events:
        db.add(ProductEvent(product_id=product.id, **evt))

    await db.commit()
    print("[Init] Smart Greenhouse product created: smart_greenhouse")
    print(f"  - Properties: {len(properties)}")
    print(f"  - Services: {len(services)}")
    print(f"  - Events: {len(events)}")
