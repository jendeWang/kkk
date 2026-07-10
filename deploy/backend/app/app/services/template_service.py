from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import (
    User, Product, ProductProperty, ProductService, ProductEvent,
    PropertyDataType, PropertyAccessType, Device, DeviceStatus,
    DeviceShadow, DeviceGroup, DeviceGroupMember, AutomationScene,
    TriggerType, ActionType, AlertRule, AlertSeverity, AlertType,
    ConditionOperator,
)
from .init_service import UI_SPECS_CONFIG, refresh_product_ui_specs
import string
import random


def _generate_key(length: int = 16) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


PRODUCT_TEMPLATES = [
    {
        "template_id": "greenhouse_basic",
        "name": "智慧大棚 · 基础版",
        "description": "适合小型种植户，包含温湿度、土壤湿度、光照等核心传感器，支持通风、补光、灌溉基础控制。",
        "icon": "🌱",
        "category": "农业",
        "level": "入门",
        "sensor_count": 4,
        "actuator_count": 3,
        "alert_count": 3,
        "scene_count": 2,
        "tags": ["温湿度", "土壤", "补光", "灌溉"],
    },
    {
        "template_id": "greenhouse_standard",
        "name": "智慧大棚 · 标准版",
        "description": "适合中型农场，包含空气/土壤温湿度、光照、CO₂等6种传感器，支持通风、补光、灌溉、加热控制，配套告警规则和自动化场景。",
        "icon": "🏡",
        "category": "农业",
        "level": "推荐",
        "sensor_count": 6,
        "actuator_count": 4,
        "alert_count": 5,
        "scene_count": 4,
        "tags": ["全功能", "自动化", "告警", "推荐"],
    },
    {
        "template_id": "greenhouse_pro",
        "name": "智慧大棚 · 高级版",
        "description": "适合大型种植基地/科研用途，包含10+传感器（氮磷钾、pH、EC、叶面温湿度等），完整执行器控制，丰富的自动化策略和数据分析。",
        "icon": "🏢",
        "category": "农业",
        "level": "专业",
        "sensor_count": 12,
        "actuator_count": 6,
        "alert_count": 8,
        "scene_count": 6,
        "tags": ["科研级", "精准农业", "水肥一体"],
    },
    {
        "template_id": "livestock_basic",
        "name": "智慧养殖 · 基础版",
        "description": "适合畜禽养殖户，监测温度、湿度、氨气、硫化氢等环境指标，支持通风和加热控制，保障畜禽生长环境。",
        "icon": "🐔",
        "category": "畜牧",
        "level": "入门",
        "sensor_count": 5,
        "actuator_count": 3,
        "alert_count": 4,
        "scene_count": 3,
        "tags": ["畜禽", "环境监测", "氨气"],
    },
]


def _get_basic_properties():
    return [
        {"identifier": "temperature", "name": "空气温度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "℃",
         "min_value": "-40", "max_value": "85", "step": "0.1", "required": True,
         "specs": {**UI_SPECS_CONFIG.get("temperature", {}), "unit": "℃"}},
        {"identifier": "humidity", "name": "空气湿度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "%RH",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {**UI_SPECS_CONFIG.get("humidity", {}), "unit": "%RH"}},
        {"identifier": "soil_moisture", "name": "土壤湿度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "%",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {**UI_SPECS_CONFIG.get("soil_moisture", {}), "unit": "%"}},
        {"identifier": "light_intensity", "name": "光照强度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "lux",
         "min_value": "0", "max_value": "100000", "step": "1", "required": True,
         "specs": {**UI_SPECS_CONFIG.get("light_intensity", {}), "unit": "lux"}},
        {"identifier": "fan_status", "name": "通风扇状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {**UI_SPECS_CONFIG.get("fan_status", {})}},
        {"identifier": "light_status", "name": "补光灯状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {**UI_SPECS_CONFIG.get("light_status", {})}},
        {"identifier": "pump_status", "name": "灌溉水泵状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {**UI_SPECS_CONFIG.get("pump_status", {})}},
        {"identifier": "work_mode", "name": "工作模式", "data_type": PropertyDataType.ENUM,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "enum_values": ["manual", "auto"], "default_value": "manual",
         "required": False, "specs": {"enum": ["manual", "auto"]}},
    ]


def _get_standard_properties():
    basic = _get_basic_properties()
    extra = [
        {"identifier": "co2", "name": "CO₂浓度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "ppm",
         "min_value": "0", "max_value": "5000", "step": "1", "required": False,
         "specs": {**UI_SPECS_CONFIG.get("co2", {}), "unit": "ppm"}},
        {"identifier": "soil_temperature", "name": "土壤温度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "℃",
         "min_value": "-20", "max_value": "60", "step": "0.1", "required": False,
         "specs": {**UI_SPECS_CONFIG.get("soil_temperature", {}), "unit": "℃"}},
        {"identifier": "brightness", "name": "补光灯亮度", "data_type": PropertyDataType.INT,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "%",
         "min_value": "0", "max_value": "100", "step": "1", "required": False,
         "specs": {"min": 0, "max": 100, "step": 1, "unit": "%"}},
    ]
    return basic + extra


def _get_pro_properties():
    standard = _get_standard_properties()
    extra = [
        {"identifier": "soil_ph", "name": "土壤pH值", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "",
         "min_value": "0", "max_value": "14", "step": "0.01", "required": False,
         "specs": {"unit": "", "normal_min": 5.5, "normal_max": 7.5}},
        {"identifier": "ec_value", "name": "土壤电导率", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "mS/cm",
         "min_value": "0", "max_value": "10", "step": "0.01", "required": False,
         "specs": {"unit": "mS/cm"}},
        {"identifier": "soil_nitrogen", "name": "土壤氮含量", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "mg/kg",
         "min_value": "0", "max_value": "500", "step": "0.1", "required": False,
         "specs": {"unit": "mg/kg"}},
        {"identifier": "soil_phosphorus", "name": "土壤磷含量", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "mg/kg",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": False,
         "specs": {"unit": "mg/kg"}},
        {"identifier": "soil_potassium", "name": "土壤钾含量", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "mg/kg",
         "min_value": "0", "max_value": "500", "step": "0.1", "required": False,
         "specs": {"unit": "mg/kg"}},
        {"identifier": "leaf_temperature", "name": "叶面温度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "℃",
         "min_value": "-20", "max_value": "60", "step": "0.1", "required": False,
         "specs": {"unit": "℃"}},
        {"identifier": "wind_speed", "name": "风速", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "m/s",
         "min_value": "0", "max_value": "20", "step": "0.1", "required": False,
         "specs": {"unit": "m/s"}},
    ]
    return standard + extra


def _get_livestock_properties():
    return [
        {"identifier": "temperature", "name": "舍内温度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "℃",
         "min_value": "-20", "max_value": "50", "step": "0.1", "required": True,
         "specs": {"unit": "℃", "normal_min": 18, "normal_max": 28}},
        {"identifier": "humidity", "name": "舍内湿度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "%RH",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {"unit": "%RH", "normal_min": 40, "normal_max": 70}},
        {"identifier": "ammonia", "name": "氨气浓度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "ppm",
         "min_value": "0", "max_value": "100", "step": "0.1", "required": True,
         "specs": {"unit": "ppm", "normal_min": 0, "normal_max": 15}},
        {"identifier": "hydrogen_sulfide", "name": "硫化氢浓度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "ppm",
         "min_value": "0", "max_value": "50", "step": "0.1", "required": False,
         "specs": {"unit": "ppm", "normal_min": 0, "normal_max": 5}},
        {"identifier": "co2", "name": "CO₂浓度", "data_type": PropertyDataType.FLOAT,
         "access_type": PropertyAccessType.READ_ONLY, "unit": "ppm",
         "min_value": "0", "max_value": "5000", "step": "1", "required": False,
         "specs": {"unit": "ppm", "normal_min": 400, "normal_max": 1500}},
        {"identifier": "fan_status", "name": "通风扇状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {"ui_type": "actuator"}},
        {"identifier": "heater_status", "name": "加热器状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {"ui_type": "actuator"}},
        {"identifier": "water_valve_status", "name": "饮水阀状态", "data_type": PropertyDataType.BOOL,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "required": False, "specs": {"ui_type": "actuator"}},
        {"identifier": "work_mode", "name": "工作模式", "data_type": PropertyDataType.ENUM,
         "access_type": PropertyAccessType.READ_WRITE, "unit": "",
         "enum_values": ["manual", "auto"], "default_value": "manual",
         "required": False, "specs": {"enum": ["manual", "auto"]}},
    ]


def _get_basic_services():
    return [
        {"identifier": "set_fan", "name": "设置通风扇", "description": "开启或关闭通风扇",
         "input_params": [{"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_light", "name": "设置补光灯", "description": "控制补光灯开关",
         "input_params": [{"identifier": "status", "name": "开关状态", "dataType": "bool", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_pump", "name": "设置灌溉泵", "description": "控制灌溉水泵",
         "input_params": [{"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_mode", "name": "设置工作模式", "description": "切换手动/自动模式",
         "input_params": [{"identifier": "mode", "name": "模式", "dataType": "enum", "specs": {"enum": ["manual", "auto"]}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
    ]


def _get_standard_services():
    basic = _get_basic_services()
    extra = [
        {"identifier": "set_light_brightness", "name": "调节补光亮度", "description": "设置补光灯亮度百分比",
         "input_params": [
             {"identifier": "status", "name": "开关", "dataType": "bool", "specs": {}},
             {"identifier": "brightness", "name": "亮度", "dataType": "int", "specs": {"min": 0, "max": 100, "unit": "%"}},
         ],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
    ]
    return basic + extra


def _get_pro_services():
    standard = _get_standard_services()
    extra = [
        {"identifier": "set_fertilizer", "name": "设置施肥", "description": "控制水肥一体化施肥",
         "input_params": [
             {"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}},
             {"identifier": "ratio", "name": "肥液比例", "dataType": "int", "specs": {"min": 0, "max": 100, "unit": "%"}},
         ],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
    ]
    return standard + extra


def _get_livestock_services():
    return [
        {"identifier": "set_fan", "name": "设置通风扇", "description": "开启或关闭通风扇",
         "input_params": [{"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_heater", "name": "设置加热器", "description": "控制加热器开关",
         "input_params": [{"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_water_valve", "name": "设置饮水阀", "description": "控制自动饮水阀",
         "input_params": [{"identifier": "status", "name": "状态", "dataType": "bool", "specs": {}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
        {"identifier": "set_mode", "name": "设置工作模式", "description": "切换手动/自动模式",
         "input_params": [{"identifier": "mode", "name": "模式", "dataType": "enum", "specs": {"enum": ["manual", "auto"]}}],
         "output_params": [{"identifier": "result", "name": "执行结果", "dataType": "string", "specs": {}}]},
    ]


def _get_basic_events():
    return [
        {"identifier": "high_temp_alert", "name": "高温告警", "event_type": "warning",
         "description": "温度超过设定阈值",
         "output_params": [
             {"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {"unit": "℃"}},
             {"identifier": "threshold", "name": "阈值", "dataType": "float", "specs": {"unit": "℃"}},
         ]},
        {"identifier": "soil_dry_alert", "name": "土壤干旱告警", "event_type": "warning",
         "description": "土壤湿度过低",
         "output_params": [
             {"identifier": "current_moisture", "name": "当前湿度", "dataType": "float", "specs": {"unit": "%"}},
             {"identifier": "threshold", "name": "阈值", "dataType": "float", "specs": {"unit": "%"}},
         ]},
    ]


def _get_standard_events():
    basic = _get_basic_events()
    extra = [
        {"identifier": "high_humidity_alert", "name": "高湿告警", "event_type": "warning",
         "description": "湿度过高",
         "output_params": [
             {"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {"unit": "%"}},
             {"identifier": "threshold", "name": "阈值", "dataType": "float", "specs": {"unit": "%"}},
         ]},
        {"identifier": "low_light_alert", "name": "光照不足告警", "event_type": "info",
         "description": "光照强度过低",
         "output_params": [
             {"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {"unit": "lux"}},
             {"identifier": "threshold", "name": "阈值", "dataType": "float", "specs": {"unit": "lux"}},
         ]},
        {"identifier": "device_offline", "name": "设备离线", "event_type": "error",
         "description": "设备与平台断开连接",
         "output_params": [{"identifier": "device_name", "name": "设备名称", "dataType": "string", "specs": {}}]},
    ]
    return basic + extra


def _get_pro_events():
    standard = _get_standard_events()
    extra = [
        {"identifier": "ph_abnormal_alert", "name": "pH异常告警", "event_type": "warning",
         "description": "土壤pH值超出正常范围",
         "output_params": [
             {"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {}},
             {"identifier": "min_threshold", "name": "下限", "dataType": "float", "specs": {}},
             {"identifier": "max_threshold", "name": "上限", "dataType": "float", "specs": {}},
         ]},
        {"identifier": "nutrient_deficiency_alert", "name": "养分不足告警", "event_type": "info",
         "description": "土壤养分低于推荐值",
         "output_params": [
             {"identifier": "nutrient_type", "name": "养分类型", "dataType": "string", "specs": {}},
             {"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {"unit": "mg/kg"}},
         ]},
    ]
    return standard + extra


def _get_livestock_events():
    return [
        {"identifier": "high_temp_alert", "name": "高温告警", "event_type": "warning",
         "description": "舍内温度过高",
         "output_params": [{"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {"unit": "℃"}}]},
        {"identifier": "high_ammonia_alert", "name": "氨气超标告警", "event_type": "error",
         "description": "氨气浓度超标，危害畜禽健康",
         "output_params": [{"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {"unit": "ppm"}}]},
        {"identifier": "high_h2s_alert", "name": "硫化氢超标告警", "event_type": "error",
         "description": "硫化氢浓度超标",
         "output_params": [{"identifier": "current_value", "name": "当前值", "dataType": "float", "specs": {"unit": "ppm"}}]},
        {"identifier": "device_offline", "name": "设备离线", "event_type": "error",
         "description": "设备与平台断开连接",
         "output_params": [{"identifier": "device_name", "name": "设备名称", "dataType": "string", "specs": {}}]},
    ]


def _get_template_config(template_id: str) -> dict | None:
    configs = {
        "greenhouse_basic": {
            "product_name": "智慧大棚(基础版)",
            "category": "农业",
            "model": "GH-BASIC",
            "properties": _get_basic_properties(),
            "services": _get_basic_services(),
            "events": _get_basic_events(),
            "default_device_name": "大棚01号",
            "alert_rules": [
                {"name": "高温告警", "property_identifier": "temperature", "operator": ConditionOperator.GT,
                 "threshold_value": "30", "severity": AlertSeverity.WARNING},
                {"name": "土壤干旱告警", "property_identifier": "soil_moisture", "operator": ConditionOperator.LT,
                 "threshold_value": "30", "severity": AlertSeverity.WARNING},
                {"name": "设备离线告警", "alert_type": AlertType.DEVICE_OFFLINE, "severity": AlertSeverity.ERROR},
            ],
            "scenes": [
                {"name": "高温自动通风", "trigger_prop": "temperature", "operator": "gt",
                 "threshold": "30", "service": "set_fan", "param": True, "cooldown": 60},
                {"name": "干旱自动灌溉", "trigger_prop": "soil_moisture", "operator": "lt",
                 "threshold": "30", "service": "set_pump", "param": True, "cooldown": 300},
            ],
        },
        "greenhouse_standard": {
            "product_name": "智慧大棚(标准版)",
            "category": "农业",
            "model": "GH-STD",
            "properties": _get_standard_properties(),
            "services": _get_standard_services(),
            "events": _get_standard_events(),
            "default_device_name": "大棚01号",
            "alert_rules": [
                {"name": "高温告警", "property_identifier": "temperature", "operator": ConditionOperator.GT,
                 "threshold_value": "30", "severity": AlertSeverity.WARNING},
                {"name": "低温告警", "property_identifier": "temperature", "operator": ConditionOperator.LT,
                 "threshold_value": "15", "severity": AlertSeverity.WARNING},
                {"name": "高湿告警", "property_identifier": "humidity", "operator": ConditionOperator.GT,
                 "threshold_value": "80", "severity": AlertSeverity.WARNING},
                {"name": "土壤干旱告警", "property_identifier": "soil_moisture", "operator": ConditionOperator.LT,
                 "threshold_value": "40", "severity": AlertSeverity.WARNING},
                {"name": "设备离线告警", "alert_type": AlertType.DEVICE_OFFLINE, "severity": AlertSeverity.ERROR},
            ],
            "scenes": [
                {"name": "高温自动通风", "trigger_prop": "temperature", "operator": "gt",
                 "threshold": "30", "service": "set_fan", "param": True, "cooldown": 60},
                {"name": "低温自动保温", "trigger_prop": "temperature", "operator": "lt",
                 "threshold": "15", "service": "set_fan", "param": False, "cooldown": 60},
                {"name": "干旱自动灌溉", "trigger_prop": "soil_moisture", "operator": "lt",
                 "threshold": "40", "service": "set_pump", "param": True, "cooldown": 300},
                {"name": "弱光自动补光", "trigger_prop": "light_intensity", "operator": "lt",
                 "threshold": "5000", "service": "set_light", "param": True, "cooldown": 120},
            ],
        },
        "greenhouse_pro": {
            "product_name": "智慧大棚(高级版)",
            "category": "农业",
            "model": "GH-PRO",
            "properties": _get_pro_properties(),
            "services": _get_pro_services(),
            "events": _get_pro_events(),
            "default_device_name": "大棚01号",
            "alert_rules": [
                {"name": "高温告警", "property_identifier": "temperature", "operator": ConditionOperator.GT,
                 "threshold_value": "32", "severity": AlertSeverity.WARNING},
                {"name": "低温告警", "property_identifier": "temperature", "operator": ConditionOperator.LT,
                 "threshold_value": "12", "severity": AlertSeverity.WARNING},
                {"name": "高湿告警", "property_identifier": "humidity", "operator": ConditionOperator.GT,
                 "threshold_value": "85", "severity": AlertSeverity.WARNING},
                {"name": "土壤干旱告警", "property_identifier": "soil_moisture", "operator": ConditionOperator.LT,
                 "threshold_value": "40", "severity": AlertSeverity.WARNING},
                {"name": "土壤过湿告警", "property_identifier": "soil_moisture", "operator": ConditionOperator.GT,
                 "threshold_value": "85", "severity": AlertSeverity.WARNING},
                {"name": "CO₂超标告警", "property_identifier": "co2", "operator": ConditionOperator.GT,
                 "threshold_value": "1500", "severity": AlertSeverity.WARNING},
                {"name": "pH异常告警", "property_identifier": "soil_ph", "operator": ConditionOperator.LT,
                 "threshold_value": "5.5", "severity": AlertSeverity.INFO},
                {"name": "设备离线告警", "alert_type": AlertType.DEVICE_OFFLINE, "severity": AlertSeverity.ERROR},
            ],
            "scenes": [
                {"name": "高温自动通风", "trigger_prop": "temperature", "operator": "gt",
                 "threshold": "32", "service": "set_fan", "param": True, "cooldown": 60},
                {"name": "低温自动保温", "trigger_prop": "temperature", "operator": "lt",
                 "threshold": "12", "service": "set_fan", "param": False, "cooldown": 60},
                {"name": "干旱自动灌溉", "trigger_prop": "soil_moisture", "operator": "lt",
                 "threshold": "40", "service": "set_pump", "param": True, "cooldown": 300},
                {"name": "弱光自动补光", "trigger_prop": "light_intensity", "operator": "lt",
                 "threshold": "5000", "service": "set_light", "param": True, "cooldown": 120},
                {"name": "过湿停止灌溉", "trigger_prop": "soil_moisture", "operator": "gt",
                 "threshold": "85", "service": "set_pump", "param": False, "cooldown": 60},
                {"name": "CO₂超标通风", "trigger_prop": "co2", "operator": "gt",
                 "threshold": "1500", "service": "set_fan", "param": True, "cooldown": 120},
            ],
        },
        "livestock_basic": {
            "product_name": "智慧养殖(基础版)",
            "category": "畜牧",
            "model": "LS-BASIC",
            "properties": _get_livestock_properties(),
            "services": _get_livestock_services(),
            "events": _get_livestock_events(),
            "default_device_name": "鸡舍01号",
            "alert_rules": [
                {"name": "高温告警", "property_identifier": "temperature", "operator": ConditionOperator.GT,
                 "threshold_value": "30", "severity": AlertSeverity.WARNING},
                {"name": "低温告警", "property_identifier": "temperature", "operator": ConditionOperator.LT,
                 "threshold_value": "18", "severity": AlertSeverity.WARNING},
                {"name": "氨气超标告警", "property_identifier": "ammonia", "operator": ConditionOperator.GT,
                 "threshold_value": "15", "severity": AlertSeverity.ERROR},
                {"name": "设备离线告警", "alert_type": AlertType.DEVICE_OFFLINE, "severity": AlertSeverity.ERROR},
            ],
            "scenes": [
                {"name": "高温自动通风", "trigger_prop": "temperature", "operator": "gt",
                 "threshold": "28", "service": "set_fan", "param": True, "cooldown": 60},
                {"name": "低温自动加热", "trigger_prop": "temperature", "operator": "lt",
                 "threshold": "18", "service": "set_heater", "param": True, "cooldown": 60},
                {"name": "氨气超标通风", "trigger_prop": "ammonia", "operator": "gt",
                 "threshold": "10", "service": "set_fan", "param": True, "cooldown": 30},
            ],
        },
    }
    return configs.get(template_id)


def list_templates():
    """返回模板列表"""
    return PRODUCT_TEMPLATES


async def create_product_from_template(
    db: AsyncSession,
    current_user: User,
    template_id: str,
    custom_name: str | None = None,
    create_default_device: bool = True,
    create_alert_rules: bool = True,
    create_scenes: bool = True,
) -> Product:
    """从模板创建产品，包含属性、服务、事件、可选默认设备/告警/场景"""
    from sqlalchemy.orm import selectinload

    cfg = _get_template_config(template_id)
    if not cfg:
        raise ValueError(f"Template not found: {template_id}")

    product_key = _generate_key()
    product_name = custom_name or cfg["product_name"]

    product = Product(
        product_key=product_key,
        name=product_name,
        category=cfg["category"],
        model=cfg["model"],
        manufacturer="IoT Platform",
        description=f"从模板创建的{product_name}",
        tsl_version="1.0",
        owner_id=current_user.id,
    )
    db.add(product)
    await db.flush()

    # 创建属性
    for prop_data in cfg["properties"]:
        db.add(ProductProperty(product_id=product.id, **prop_data))

    # 创建服务
    for svc_data in cfg["services"]:
        db.add(ProductService(product_id=product.id, **svc_data))

    # 创建事件
    for evt_data in cfg["events"]:
        db.add(ProductEvent(product_id=product.id, **evt_data))

    await db.flush()

    # 刷新UI配置
    await refresh_product_ui_specs(db, product.id)

    default_device = None
    if create_default_device:
        # 创建默认设备
        device_key = _generate_key(10)
        device_secret = _generate_key(20)
        device = Device(
            device_key=device_key,
            device_secret=device_secret,
            device_name=cfg["default_device_name"],
            product_id=product.id,
            status=DeviceStatus.ONLINE,
            owner_id=current_user.id,
        )
        db.add(device)
        await db.flush()

        # 创建设备影子
        shadow = DeviceShadow(
            device_id=device.id,
            reported={},
            desired={},
        )
        db.add(shadow)
        default_device = device

        # 加入第一个分组
        group_result = await db.execute(
            select(DeviceGroup).where(
                DeviceGroup.owner_id == current_user.id,
            ).order_by(DeviceGroup.id.asc()).limit(1)
        )
        group = group_result.scalar_one_or_none()
        if group:
            member = DeviceGroupMember(group_id=group.id, device_id=device.id)
            db.add(member)

    # 创建告警规则
    if create_alert_rules and default_device:
        for rule_data in cfg.get("alert_rules", []):
            alert_type = rule_data.get("alert_type", AlertType.THRESHOLD)
            rule = AlertRule(
                name=rule_data["name"],
                description=f"模板预设 - {rule_data['name']}",
                alert_type=alert_type,
                product_id=product.id,
                device_id=default_device.id if alert_type == AlertType.THRESHOLD else None,
                property_identifier=rule_data.get("property_identifier"),
                operator=rule_data.get("operator", ConditionOperator.GT),
                threshold_value=rule_data.get("threshold_value"),
                severity=rule_data.get("severity", AlertSeverity.WARNING),
                enabled=True,
                owner_id=current_user.id,
            )
            db.add(rule)

    # 创建自动化场景
    if create_scenes and default_device:
        for scene_data in cfg.get("scenes", []):
            scene = AutomationScene(
                name=scene_data["name"],
                description=f"模板预设 - 当{scene_data['trigger_prop']} {scene_data['operator']} {scene_data['threshold']}时，自动{scene_data['service']}",
                owner_id=current_user.id,
                trigger_type=TriggerType.THRESHOLD,
                trigger_config={
                    "device_id": default_device.id,
                    "property_identifier": scene_data["trigger_prop"],
                    "operator": scene_data["operator"],
                    "threshold_value": scene_data["threshold"],
                },
                action_type=ActionType.COMMAND,
                action_config=[{
                    "device_id": default_device.id,
                    "service_identifier": scene_data["service"],
                    "input_params": {"status": scene_data["param"]},
                }],
                enabled=True,
                cooldown_seconds=scene_data["cooldown"],
            )
            db.add(scene)

    await db.commit()

    # 重新加载产品完整信息
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.properties),
            selectinload(Product.services),
            selectinload(Product.events),
        )
        .where(Product.id == product.id)
    )
    product = result.scalar_one()
    return product
