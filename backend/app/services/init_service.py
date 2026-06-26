from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import (
    User, Product, ProductProperty, ProductService, ProductEvent,
    PropertyDataType, PropertyAccessType, DeviceGroup, DeviceGroupMember, Device,
    AutomationScene, TriggerType, ActionType
)
from ..security.auth import get_password_hash
from ..config import settings


UI_SPECS_CONFIG = {
    "temperature": {
        "ui_type": "sensor",
        "ui_icon": "🌡️",
        "ui_color": "#f56c6c",
        "ui_unit": "℃",
        "ui_decimals": 1,
        "ui_normal_min": 15,
        "ui_normal_max": 30,
        "ui_default_x": 100,
        "ui_default_y": 100,
    },
    "humidity": {
        "ui_type": "sensor",
        "ui_icon": "💧",
        "ui_color": "#409eff",
        "ui_unit": "%RH",
        "ui_decimals": 1,
        "ui_normal_min": 40,
        "ui_normal_max": 70,
        "ui_default_x": 280,
        "ui_default_y": 100,
    },
    "light_intensity": {
        "ui_type": "sensor",
        "ui_icon": "☀️",
        "ui_color": "#e6a23c",
        "ui_unit": "lux",
        "ui_decimals": 0,
        "ui_normal_min": 1000,
        "ui_normal_max": 50000,
        "ui_default_x": 460,
        "ui_default_y": 100,
    },
    "soil_moisture": {
        "ui_type": "sensor",
        "ui_icon": "🌱",
        "ui_color": "#67c23a",
        "ui_unit": "%",
        "ui_decimals": 1,
        "ui_normal_min": 30,
        "ui_normal_max": 80,
        "ui_default_x": 190,
        "ui_default_y": 280,
    },
    "co2": {
        "ui_type": "sensor",
        "ui_icon": "💨",
        "ui_color": "#909399",
        "ui_unit": "ppm",
        "ui_decimals": 0,
        "ui_normal_min": 400,
        "ui_normal_max": 1500,
        "ui_default_x": 640,
        "ui_default_y": 100,
    },
    "soil_temperature": {
        "ui_type": "sensor",
        "ui_icon": "🪴",
        "ui_color": "#8e44ad",
        "ui_unit": "℃",
        "ui_decimals": 1,
        "ui_normal_min": 15,
        "ui_normal_max": 28,
        "ui_default_x": 370,
        "ui_default_y": 280,
    },
    "fan_status": {
        "ui_type": "actuator",
        "ui_icon": "🌀",
        "ui_color": "#409eff",
        "ui_service": "set_fan",
        "ui_service_param": "status",
        "ui_default_x": 100,
        "ui_default_y": 440,
    },
    "light_status": {
        "ui_type": "actuator",
        "ui_icon": "💡",
        "ui_color": "#e6a23c",
        "ui_service": "set_light",
        "ui_service_param": "status",
        "ui_default_x": 340,
        "ui_default_y": 440,
    },
    "pump_status": {
        "ui_type": "actuator",
        "ui_icon": "🚿",
        "ui_color": "#67c23a",
        "ui_service": "set_pump",
        "ui_service_param": "status",
        "ui_default_x": 580,
        "ui_default_y": 440,
    },
}


async def refresh_product_ui_specs(db: AsyncSession, product_id: int) -> int:
    """根据identifier为产品属性补充UI配置，返回更新的属性数量"""
    from sqlalchemy.orm import selectinload, attributes

    result = await db.execute(
        select(Product)
        .options(selectinload(Product.properties))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        return 0

    updated_count = 0
    for prop in product.properties:
        ui_config = UI_SPECS_CONFIG.get(prop.identifier)
        if not ui_config:
            continue

        current_specs = dict(prop.specs or {})
        needs_update = False
        for key, value in ui_config.items():
            if key not in current_specs or current_specs[key] != value:
                current_specs[key] = value
                needs_update = True

        if needs_update:
            prop.specs = current_specs
            attributes.flag_modified(prop, "specs")
            updated_count += 1

    if updated_count > 0:
        await db.commit()

    return updated_count


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
        updated = await refresh_product_ui_specs(db, existing.id)
        if updated > 0:
            print(f"[Init] Smart Greenhouse product UI specs updated: {updated} properties")
        else:
            print("[Init] Smart Greenhouse product already exists, UI specs up to date")
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
         "specs": {"min": -40, "max": 85, "step": 0.1, "unit": "℃", **UI_SPECS_CONFIG["temperature"]}},
        {"identifier": "humidity", "name": "空气湿度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "%RH",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {"min": 0, "max": 100, "step": 0.1, "unit": "%RH", **UI_SPECS_CONFIG["humidity"]}},
        {"identifier": "light_intensity", "name": "光照强度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "lux",
         "min_value": "0", "max_value": "100000", "step": "1", "required": True,
         "specs": {"min": 0, "max": 100000, "step": 1, "unit": "lux", **UI_SPECS_CONFIG["light_intensity"]}},
        {"identifier": "soil_moisture", "name": "土壤湿度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "%",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {"min": 0, "max": 100, "step": 0.1, "unit": "%", **UI_SPECS_CONFIG["soil_moisture"]}},
        {"identifier": "co2", "name": "CO₂浓度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "ppm",
         "min_value": "0", "max_value": "5000", "step": "1", "required": False,
         "specs": {"min": 0, "max": 5000, "step": 1, "unit": "ppm", **UI_SPECS_CONFIG["co2"]}},
        {"identifier": "soil_temperature", "name": "土壤温度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "℃",
         "min_value": "-20", "max_value": "60", "step": "0.1", "required": False,
         "specs": {"min": -20, "max": 60, "step": 0.1, "unit": "℃", **UI_SPECS_CONFIG["soil_temperature"]}},
        {"identifier": "fan_status", "name": "通风扇状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {**UI_SPECS_CONFIG["fan_status"]}},
        {"identifier": "light_status", "name": "补光灯状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {**UI_SPECS_CONFIG["light_status"]}},
        {"identifier": "pump_status", "name": "灌溉水泵状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {**UI_SPECS_CONFIG["pump_status"]}},
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


async def init_default_group(db: AsyncSession):
    """为每个用户创建默认3个大棚分组，并将已有设备加入"""
    result = await db.execute(select(User))
    users = result.scalars().all()

    for user in users:
        # 检查是否已经有预设分组
        existing_groups_result = await db.execute(
            select(DeviceGroup).where(
                DeviceGroup.owner_id == user.id,
            )
        )
        existing_groups = existing_groups_result.scalars().all()
        
        if len(existing_groups) >= 3:
            print(f"[Init] Default groups already exist for user: {user.username}")
            continue

        # 创建3个大棚分组
        default_groups = [
            {"name": "1号大棚", "description": "第1号种植大棚"},
            {"name": "2号大棚", "description": "第2号种植大棚"},
            {"name": "3号大棚", "description": "第3号种植大棚"},
        ]

        for group_data in default_groups:
            group_result = await db.execute(
                select(DeviceGroup).where(
                    DeviceGroup.name == group_data["name"],
                    DeviceGroup.owner_id == user.id,
                )
            )
            existing_group = group_result.scalar_one_or_none()
            if existing_group:
                continue

            new_group = DeviceGroup(
                name=group_data["name"],
                description=group_data["description"],
                owner_id=user.id,
            )
            db.add(new_group)
            await db.flush()

            # 如果是第1号大棚，自动将已有设备加入
            if group_data["name"] == "1号大棚":
                devices_result = await db.execute(
                    select(Device.id).where(Device.owner_id == user.id)
                )
                device_ids = [row[0] for row in devices_result.all()]

                for device_id in device_ids:
                    member = DeviceGroupMember(
                        group_id=new_group.id,
                        device_id=device_id,
                    )
                    db.add(member)

        await db.commit()
        print(f"[Init] Default greenhouse groups (3) created for user: {user.username}")


async def init_default_scenes(db: AsyncSession):
    """为智慧大棚产品创建预置自动化场景（需要已存在设备）"""
    user_result = await db.execute(select(User).where(User.username == "admin"))
    admin = user_result.scalar_one_or_none()
    if not admin:
        return

    product_result = await db.execute(
        select(Product).where(
            Product.product_key == "smart_greenhouse",
            Product.owner_id == admin.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        return

    device_result = await db.execute(
        select(Device).where(
            Device.product_id == product.id,
            Device.owner_id == admin.id,
        ).limit(1)
    )
    device = device_result.scalar_one_or_none()
    if not device:
        print("[Init] No greenhouse device found, skipping default scenes")
        return

    scenes_to_create = [
        {
            "name": "高温自动通风",
            "description": "当空气温度超过30°C时，自动打开通风扇降温",
            "trigger_type": TriggerType.THRESHOLD,
            "trigger_config": {
                "device_id": device.id,
                "property_identifier": "temperature",
                "operator": "gt",
                "threshold_value": "30",
            },
            "action_type": ActionType.COMMAND,
            "action_config": [
                {
                    "device_id": device.id,
                    "service_identifier": "set_fan",
                    "input_params": {"status": True},
                }
            ],
            "enabled": True,
            "cooldown_seconds": 60,
        },
        {
            "name": "低温自动保温",
            "description": "当空气温度低于15°C时，自动关闭通风扇保温",
            "trigger_type": TriggerType.THRESHOLD,
            "trigger_config": {
                "device_id": device.id,
                "property_identifier": "temperature",
                "operator": "lt",
                "threshold_value": "15",
            },
            "action_type": ActionType.COMMAND,
            "action_config": [
                {
                    "device_id": device.id,
                    "service_identifier": "set_fan",
                    "input_params": {"status": False},
                }
            ],
            "enabled": True,
            "cooldown_seconds": 60,
        },
        {
            "name": "干旱自动灌溉",
            "description": "当土壤湿度低于30%时，自动打开灌溉水泵",
            "trigger_type": TriggerType.THRESHOLD,
            "trigger_config": {
                "device_id": device.id,
                "property_identifier": "soil_moisture",
                "operator": "lt",
                "threshold_value": "30",
            },
            "action_type": ActionType.COMMAND,
            "action_config": [
                {
                    "device_id": device.id,
                    "service_identifier": "set_pump",
                    "input_params": {"status": True, "duration": 60},
                }
            ],
            "enabled": True,
            "cooldown_seconds": 300,
        },
    ]

    created_count = 0
    for scene_data in scenes_to_create:
        existing_result = await db.execute(
            select(AutomationScene).where(
                AutomationScene.name == scene_data["name"],
                AutomationScene.owner_id == admin.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            continue

        scene = AutomationScene(
            name=scene_data["name"],
            description=scene_data["description"],
            owner_id=admin.id,
            trigger_type=scene_data["trigger_type"],
            trigger_config=scene_data["trigger_config"],
            action_type=scene_data["action_type"],
            action_config=scene_data["action_config"],
            enabled=scene_data["enabled"],
            cooldown_seconds=scene_data["cooldown_seconds"],
        )
        db.add(scene)
        created_count += 1

    if created_count > 0:
        await db.commit()
        print(f"[Init] {created_count} default automation scenes created for device: {device.device_name}")
    else:
        print("[Init] Default automation scenes already exist")
