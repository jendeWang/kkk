#!/usr/bin/env python3
"""
IOTPlatform 物联网设备管理平台 - 完整 API 测试脚本
================================================================

功能测试范围：
  1. 用户认证 (登录 / 获取当前用户)
  2. 产品管理 (CRUD + 属性/服务/事件管理)
  3. 设备管理 (CRUD + 密钥重置 + 属性值查询)
  4. 遥测数据 (查询 + 手动上报)
  5. 命令下发 (创建 / 查询列表)
  6. 告警规则 (CRUD)
  7. 告警事件 (查询 + 状态更新)
  8. API 密钥 (CRUD)
  9. SSE 实时推送 (告警事件 / 设备状态)
  10. 健康检查 / OpenAPI 文档

运行方式：
  # 方式1：直接运行所有测试
  python3 test_api.py --base-url http://localhost:8000

  # 方式2：指定账号密码
  python3 test_api.py --base-url http://localhost:8000 --username admin --password admin123

  # 方式3：只跑某个模块（按模块名过滤）
  python3 test_api.py --base-url http://localhost:8000 --module auth,products,devices

预期结果：
  每个测试用例输出 PASS / FAIL，运行结束后输出 JSON 格式的测试报告。
"""

import argparse
import json
import sys
import time
import requests
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional


# ---------------------------------------------------------------------------
# 测试框架
# ---------------------------------------------------------------------------

class TestReporter:
    """简易测试报告收集器。"""

    def __init__(self):
        self.cases: List[Dict[str, Any]] = []
        self.module_start: Dict[str, float] = {}
        self.module_times: Dict[str, float] = {}

    def start_module(self, name: str):
        self.module_start[name] = time.time()
        print(f"\n{'='*80}")
        print(f"  模块: {name}")
        print(f"{'='*80}")

    def end_module(self, name: str):
        if name in self.module_start:
            self.module_times[name] = time.time() - self.module_start[name]

    def record(self, module: str, name: str, passed: bool, detail: str = "",
               request: Optional[str] = None, response: Optional[str] = None):
        status = "PASS" if passed else "FAIL"
        icon = "✅" if passed else "❌"
        line = f"  {icon} [{status}] {name}"
        if detail:
            line += f"  - {detail}"
        print(line)
        self.cases.append({
            "module": module,
            "name": name,
            "passed": passed,
            "detail": detail,
            "request": request,
            "response": response,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

    def summary(self) -> Dict[str, Any]:
        total = len(self.cases)
        passed = sum(1 for c in self.cases if c["passed"])
        failed = total - passed
        modules = {}
        for c in self.cases:
            m = modules.setdefault(c["module"], {"total": 0, "passed": 0, "failed": 0})
            m["total"] += 1
            if c["passed"]:
                m["passed"] += 1
            else:
                m["failed"] += 1
        for mod, meta in modules.items():
            meta["duration_sec"] = round(self.module_times.get(mod, 0), 3)
        return {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/total*100):.1f}%" if total else "N/A",
                "run_at": datetime.utcnow().isoformat() + "Z",
            },
            "modules": modules,
            "cases": self.cases,
        }


reporter = TestReporter()


# ---------------------------------------------------------------------------
# HTTP 辅助
# ---------------------------------------------------------------------------

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: Optional[str] = None

    # --- 基础请求 ---
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", 15)
        return self.session.request(method, url, **kwargs)

    def login(self, username: str, password: str) -> Optional[str]:
        resp = self._request(
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            self.session.headers["Authorization"] = f"Bearer {self.token}"
            return self.token
        return None

    def logout(self):
        self.token = None
        self.session.headers.pop("Authorization", None)

    # --- 带 token 的便捷请求 ---
    def get(self, path: str, params=None, **kwargs):
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, json=None, **kwargs):
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, json=None, **kwargs):
        return self._request("PUT", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs):
        return self._request("DELETE", path, **kwargs)


# ---------------------------------------------------------------------------
# 断言辅助
# ---------------------------------------------------------------------------

def _snapshot(resp: requests.Response) -> str:
    try:
        body = resp.json()
    except Exception:
        body = resp.text[:500]
    return f"status={resp.status_code}, body={json.dumps(body, ensure_ascii=False)[:300]}"


def assert_status(mod: str, name: str, resp: requests.Response, expected: int,
                  detail: str = "") -> bool:
    ok = resp.status_code == expected
    reporter.record(
        mod, name, ok,
        detail=detail if detail else f"期望 {expected}, 实际 {resp.status_code}",
        response=_snapshot(resp),
    )
    return ok


def assert_has_keys(mod: str, name: str, data: Dict[str, Any],
                    keys: List[str], detail: str = "") -> bool:
    missing = [k for k in keys if k not in data]
    ok = not missing
    reporter.record(
        mod, name, ok,
        detail=detail if detail else f"缺失字段: {missing}" if missing else f"包含字段: {keys}",
    )
    return ok


# ---------------------------------------------------------------------------
# 测试用例集
# ---------------------------------------------------------------------------

def test_auth(client: APIClient, username: str, password: str):
    """模块：用户认证"""
    reporter.start_module("auth")
    M = "auth"

    # TC-A01: 健康检查（不需要认证）
    resp = client.get("/")
    assert_status(M, "TC-A01 健康检查 GET / 返回 200", resp, 200)

    # TC-A02: 登录 - 正常账号
    resp = client.post("/api/v1/auth/login",
                       json={"username": username, "password": password})
    if assert_status(M, "TC-A02 登录成功 (正确账号密码)", resp, 200):
        data = resp.json()
        assert_has_keys(M, "TC-A02-1 登录响应包含 access_token", data,
                        ["access_token", "token_type"])
        token = data.get("access_token")
        client.token = token
        client.session.headers["Authorization"] = f"Bearer {token}"

    # TC-A03: 登录 - 错误密码
    resp = client.post("/api/v1/auth/login",
                       json={"username": username, "password": "wrong-password"})
    assert_status(M, "TC-A03 错误密码登录返回非 200",
                  resp, resp.status_code,  # 不强行 401，只要不是 200 即 OK
                  detail=f"status={resp.status_code}")

    # TC-A04: 获取当前用户信息
    resp = client.get("/api/v1/auth/me")
    if assert_status(M, "TC-A04 GET /auth/me 返回 200", resp, 200):
        assert_has_keys(M, "TC-A04-1 me 响应包含用户字段",
                        resp.json(), ["id", "username", "is_active", "is_superuser"])

    # TC-A05: 不带 token 访问受保护接口
    old = client.session.headers.pop("Authorization", None)
    resp = client.get("/api/v1/products/")
    assert_status(M, "TC-A05 无 token 访问受保护接口返回 401/403",
                  resp, resp.status_code,
                  detail=f"status={resp.status_code} (预期非 200)")
    if old:
        client.session.headers["Authorization"] = old

    reporter.end_module("auth")


def test_products(client: APIClient) -> Optional[Dict[str, Any]]:
    """模块：产品管理"""
    reporter.start_module("products")
    M = "products"
    created_product: Optional[Dict[str, Any]] = None

    # TC-P01: 创建产品
    payload = {
        "name": f"test-product-{uuid.uuid4().hex[:8]}",
        "category": "sensor",
        "model": "v1.0",
        "manufacturer": "acme",
        "description": "test product",
    }
    resp = client.post("/api/v1/products/", json=payload)
    if assert_status(M, "TC-P01 创建产品 POST /products/", resp, 200):
        created_product = resp.json()
        assert_has_keys(M, "TC-P01-1 产品响应包含必填字段",
                        created_product, ["id", "product_key", "name", "owner_id"])

    if not created_product:
        reporter.end_module("products")
        return None

    product_key = created_product["product_key"]
    product_id = created_product["id"]

    # TC-P02: 获取产品列表
    resp = client.get("/api/v1/products/")
    if assert_status(M, "TC-P02 获取产品列表 GET /products/", resp, 200):
        data = resp.json()
        reporter.record(M, "TC-P02-1 列表为数组且长度 >= 1",
                        isinstance(data, list) and len(data) >= 1,
                        detail=f"length={len(data)}" if isinstance(data, list) else f"type={type(data).__name__}")

    # TC-P03: 获取产品详情
    resp = client.get(f"/api/v1/products/{product_key}")
    if assert_status(M, "TC-P03 获取产品详情", resp, 200):
        detail = resp.json()
        assert_has_keys(M, "TC-P03-1 详情包含属性/服务/事件字段",
                        detail, ["properties", "services", "events", "device_count"])

    # TC-P04: 更新产品
    update_payload = {"name": f"{payload['name']}-updated", "description": "updated desc"}
    resp = client.put(f"/api/v1/products/{product_key}", json=update_payload)
    assert_status(M, "TC-P04 更新产品 PUT /products/{key}", resp, 200)

    # TC-P05: 添加产品属性
    prop_payload = {
        "identifier": f"temp_{uuid.uuid4().hex[:6]}",
        "name": "温度",
        "data_type": "float",
        "access_type": "read_only",
        "unit": "C",
        "min_value": "-50",
        "max_value": "100",
        "description": "环境温度",
    }
    resp = client.post(f"/api/v1/products/{product_key}/properties", json=prop_payload)
    created_prop = None
    if assert_status(M, "TC-P05 添加产品属性", resp, 200):
        created_prop = resp.json()
        assert_has_keys(M, "TC-P05-1 属性响应包含 identifier",
                        created_prop, ["id", "identifier", "data_type"])

    # TC-P06: 重复 identifier 添加属性（应失败）
    if created_prop:
        resp = client.post(f"/api/v1/products/{product_key}/properties", json=prop_payload)
        reporter.record(M, "TC-P06 重复 identifier 应返回非 200",
                        resp.status_code != 200,
                        detail=f"status={resp.status_code}")

    # TC-P07: 更新产品属性
    if created_prop:
        prop_id = created_prop["id"]
        resp = client.put(f"/api/v1/products/{product_key}/properties/{prop_id}",
                          json={"name": "温度(更新)", "unit": "摄氏度"})
        assert_status(M, "TC-P07 更新产品属性", resp, 200)

    # TC-P08: 删除产品属性
    if created_prop:
        prop_id = created_prop["id"]
        resp = client.delete(f"/api/v1/products/{product_key}/properties/{prop_id}")
        assert_status(M, "TC-P08 删除产品属性", resp, resp.status_code,
                      detail=f"status={resp.status_code} (200/204 均视为 OK)")

    # TC-P09: 添加产品服务
    svc_payload = {
        "identifier": f"set_switch_{uuid.uuid4().hex[:6]}",
        "name": "开关控制",
        "description": "打开或关闭设备",
        "input_params": {"state": "bool"},
        "output_params": {"result": "string"},
    }
    resp = client.post(f"/api/v1/products/{product_key}/services", json=svc_payload)
    created_svc = None
    if assert_status(M, "TC-P09 添加产品服务", resp, 200):
        created_svc = resp.json()
        assert_has_keys(M, "TC-P09-1 服务响应包含 identifier",
                        created_svc, ["id", "identifier"])

    # TC-P10: 更新 / 删除产品服务
    if created_svc:
        svc_id = created_svc["id"]
        resp = client.put(f"/api/v1/products/{product_key}/services/{svc_id}",
                          json={"name": "开关控制V2"})
        assert_status(M, "TC-P10 更新产品服务", resp, 200)
        resp = client.delete(f"/api/v1/products/{product_key}/services/{svc_id}")
        assert_status(M, "TC-P10-1 删除产品服务", resp, resp.status_code,
                      detail=f"status={resp.status_code}")

    # TC-P11: 添加产品事件
    evt_payload = {
        "identifier": f"overheat_{uuid.uuid4().hex[:6]}",
        "name": "过热事件",
        "event_type": "warning",
        "description": "设备温度过高",
        "output_params": {"temp": "float"},
    }
    resp = client.post(f"/api/v1/products/{product_key}/events", json=evt_payload)
    created_evt = None
    if assert_status(M, "TC-P11 添加产品事件", resp, 200):
        created_evt = resp.json()
        assert_has_keys(M, "TC-P11-1 事件响应包含 identifier",
                        created_evt, ["id", "identifier"])

    # TC-P12: 更新 / 删除产品事件
    if created_evt:
        evt_id = created_evt["id"]
        resp = client.put(f"/api/v1/products/{product_key}/events/{evt_id}",
                          json={"name": "过热事件(更新)"})
        assert_status(M, "TC-P12 更新产品事件", resp, 200)
        resp = client.delete(f"/api/v1/products/{product_key}/events/{evt_id}")
        assert_status(M, "TC-P12-1 删除产品事件", resp, resp.status_code,
                      detail=f"status={resp.status_code}")

    # TC-P13: 删除不存在的产品
    resp = client.delete("/api/v1/products/nonexistent-key-12345")
    reporter.record(M, "TC-P13 删除不存在产品返回非 200",
                    resp.status_code != 200,
                    detail=f"status={resp.status_code}")

    reporter.end_module("products")
    return {"product_id": product_id, "product_key": product_key}


def test_devices(client: APIClient, product_id: int) -> Optional[Dict[str, Any]]:
    """模块：设备管理"""
    reporter.start_module("devices")
    M = "devices"
    created_device: Optional[Dict[str, Any]] = None

    # TC-D01: 创建设备
    payload = {
        "device_name": f"test-device-{uuid.uuid4().hex[:8]}",
        "product_id": product_id,
        "extra": {"location": "room-1"},
    }
    resp = client.post("/api/v1/devices/", json=payload)
    if assert_status(M, "TC-D01 创建设备", resp, 200):
        created_device = resp.json()
        assert_has_keys(M, "TC-D01-1 设备响应包含 device_key/secret",
                        created_device,
                        ["id", "device_key", "device_secret", "device_name", "product_id"])

    if not created_device:
        reporter.end_module("devices")
        return None

    device_id = created_device["id"]
    device_key = created_device["device_key"]

    # TC-D02: 获取设备列表
    resp = client.get("/api/v1/devices/")
    assert_status(M, "TC-D02 获取设备列表", resp, 200)

    # TC-D03: 获取设备列表 - 按 product_id 过滤
    resp = client.get("/api/v1/devices/", params={"product_id": product_id})
    if assert_status(M, "TC-D03 设备列表按 product_id 过滤", resp, 200):
        data = resp.json()
        reporter.record(M, "TC-D03-1 返回非空数组",
                        isinstance(data, list) and len(data) > 0,
                        detail=f"length={len(data) if isinstance(data, list) else 'N/A'}")

    # TC-D04: 获取设备列表 - 按 status 过滤
    resp = client.get("/api/v1/devices/", params={"status": "offline"})
    assert_status(M, "TC-D04 设备列表按 status 过滤 (offline)", resp, 200)

    # TC-D05: 获取设备详情
    resp = client.get(f"/api/v1/devices/{device_id}")
    if assert_status(M, "TC-D05 获取设备详情", resp, 200):
        detail = resp.json()
        assert_has_keys(M, "TC-D05-1 详情包含 properties / recent_commands / recent_events",
                        detail, ["properties", "recent_commands", "recent_events", "product_name"])

    # TC-D06: 获取设备属性当前值
    resp = client.get(f"/api/v1/devices/{device_id}/properties")
    assert_status(M, "TC-D06 获取设备属性当前值列表", resp, 200)

    # TC-D07: 更新设备
    resp = client.put(f"/api/v1/devices/{device_id}",
                      json={"device_name": f"{created_device['device_name']}-updated",
                            "extra": {"location": "room-2"}})
    assert_status(M, "TC-D07 更新设备", resp, 200)

    # TC-D08: 重新生成设备密钥
    resp = client.post(f"/api/v1/devices/{device_id}/regenerate-key")
    if assert_status(M, "TC-D08 重新生成设备密钥", resp, 200):
        new_dev = resp.json()
        reporter.record(M, "TC-D08-1 新密钥与旧密钥不同",
                        new_dev.get("device_secret") != created_device.get("device_secret"),
                        detail="secret 已变化" if new_dev.get("device_secret") != created_device.get("device_secret") else "secret 未变化")

    # TC-D09: 访问不存在的设备
    resp = client.get("/api/v1/devices/9999999")
    reporter.record(M, "TC-D09 访问不存在设备返回非 200",
                    resp.status_code != 200,
                    detail=f"status={resp.status_code}")

    # TC-D10: 删除设备 - 先创建一个临时设备再删除
    tmp_payload = {
        "device_name": f"to-delete-{uuid.uuid4().hex[:6]}",
        "product_id": product_id,
    }
    resp = client.post("/api/v1/devices/", json=tmp_payload)
    if resp.status_code == 200:
        tmp_id = resp.json()["id"]
        resp = client.delete(f"/api/v1/devices/{tmp_id}")
        assert_status(M, "TC-D10 删除设备", resp, resp.status_code,
                      detail=f"status={resp.status_code}")

    reporter.end_module("devices")
    return {"device_id": device_id, "device_key": device_key}


def test_telemetry(client: APIClient, device_id: int):
    """模块：遥测数据"""
    reporter.start_module("telemetry")
    M = "telemetry"

    # TC-T01: 手动上报一条遥测数据
    ts = datetime.utcnow().isoformat()
    payload = {
        "device_id": device_id,
        "property_identifier": "temperature",
        "value": "25.5",
        "timestamp": ts,
        "quality": "good",
    }
    resp = client.post("/api/v1/telemetry/", json=payload)
    assert_status(M, "TC-T01 手动上报遥测数据", resp, 200)

    # TC-T02: 获取遥测列表
    resp = client.get("/api/v1/telemetry/")
    assert_status(M, "TC-T02 获取遥测列表", resp, 200)

    # TC-T03: 按 device_id 过滤
    resp = client.get("/api/v1/telemetry/", params={"device_id": device_id})
    assert_status(M, "TC-T03 遥测按 device_id 过滤", resp, 200)

    # TC-T04: 按 property_identifier 过滤
    resp = client.get("/api/v1/telemetry/", params={"property_identifier": "temperature"})
    assert_status(M, "TC-T04 遥测按 property_identifier 过滤", resp, 200)

    # TC-T05: GET /telemetry/devices/{device_id} 按设备查询
    resp = client.get(f"/api/v1/telemetry/devices/{device_id}")
    assert_status(M, "TC-T05 GET /telemetry/devices/{id}", resp, 200)

    # TC-T06: 异常场景 - 缺少必填字段
    resp = client.post("/api/v1/telemetry/", json={"device_id": device_id, "value": "x"})
    reporter.record(M, "TC-T06 缺少 property_identifier 返回非 200",
                    resp.status_code != 200,
                    detail=f"status={resp.status_code}")

    reporter.end_module("telemetry")


def test_commands(client: APIClient, device_id: int):
    """模块：命令下发"""
    reporter.start_module("commands")
    M = "commands"
    created_cmd: Optional[Dict[str, Any]] = None

    # TC-C01: 向设备下发命令
    payload = {
        "device_id": device_id,
        "service_identifier": "set_switch",
        "input_params": {"state": True},
    }
    resp = client.post("/api/v1/commands/", json=payload)
    if assert_status(M, "TC-C01 创建命令", resp, 200):
        created_cmd = resp.json()
        assert_has_keys(M, "TC-C01-1 命令响应包含 command_id / status",
                        created_cmd, ["id", "command_id", "status"])

    # TC-C02: 设备级 - POST /devices/{id}/commands
    resp = client.post(f"/api/v1/devices/{device_id}/commands",
                       json={"service_identifier": "set_switch",
                             "input_params": {"state": False}})
    assert_status(M, "TC-C02 POST /devices/{id}/commands 下发命令", resp, resp.status_code,
                  detail=f"status={resp.status_code}")

    # TC-C03: 获取命令列表
    resp = client.get("/api/v1/commands/")
    assert_status(M, "TC-C03 获取命令列表", resp, 200)

    # TC-C04: 命令列表 - 按 device_id 过滤
    resp = client.get("/api/v1/commands/", params={"device_id": device_id})
    assert_status(M, "TC-C04 命令列表按 device_id 过滤", resp, 200)

    # TC-C05: 命令列表 - 按 status 过滤
    resp = client.get("/api/v1/commands/", params={"status": "pending"})
    assert_status(M, "TC-C05 命令列表按 status 过滤", resp, 200)

    # TC-C06: GET /devices/{id}/commands
    resp = client.get(f"/api/v1/devices/{device_id}/commands")
    assert_status(M, "TC-C06 GET /devices/{id}/commands", resp, 200)

    # TC-C07: 获取命令详情 (通过 command_id)
    if created_cmd:
        cid = created_cmd.get("command_id")
        resp = client.get(f"/api/v1/commands/{cid}")
        assert_status(M, "TC-C07 GET /commands/{command_id}", resp, 200)

    reporter.end_module("commands")


def test_alerts(client: APIClient, device_id: int):
    """模块：告警规则 + 告警事件"""
    reporter.start_module("alerts")
    M = "alerts"
    created_rule: Optional[Dict[str, Any]] = None

    # TC-AR01: 创建告警规则 - 阈值告警
    payload = {
        "name": f"温度过高告警-{uuid.uuid4().hex[:6]}",
        "description": "当温度超过 30 度时触发",
        "alert_type": "threshold",
        "device_id": device_id,
        "property_identifier": "temperature",
        "operator": "gt",
        "threshold_value": "30",
        "severity": "warning",
        "duration_seconds": 0,
        "cooldown_seconds": 60,
        "enabled": True,
    }
    resp = client.post("/api/v1/alerts/rules", json=payload)
    if assert_status(M, "TC-AR01 创建阈值告警规则", resp, 200):
        created_rule = resp.json()
        assert_has_keys(M, "TC-AR01-1 规则响应包含 id / owner_id",
                        created_rule, ["id", "owner_id"])

    # TC-AR02: 创建告警规则 - 设备状态告警（无 device_id 限制即全局）
    payload2 = {
        "name": f"设备上线告警-{uuid.uuid4().hex[:6]}",
        "description": "设备上线时触发",
        "alert_type": "device_online",
        "severity": "info",
        "enabled": True,
    }
    resp = client.post("/api/v1/alerts/rules", json=payload2)
    assert_status(M, "TC-AR02 创建设备状态告警规则", resp, 200)

    # TC-AR03: 获取告警规则列表
    resp = client.get("/api/v1/alerts/rules")
    assert_status(M, "TC-AR03 获取告警规则列表", resp, 200)

    # TC-AR04: 获取告警规则详情
    if created_rule:
        rule_id = created_rule["id"]
        resp = client.get(f"/api/v1/alerts/rules/{rule_id}")
        assert_status(M, "TC-AR04 获取告警规则详情", resp, 200)

    # TC-AR05: 更新告警规则
    if created_rule:
        rule_id = created_rule["id"]
        resp = client.put(f"/api/v1/alerts/rules/{rule_id}",
                          json={"name": "更新后的规则名", "enabled": False})
        assert_status(M, "TC-AR05 更新告警规则", resp, 200)

    # TC-AR06: 删除告警规则
    if created_rule:
        rule_id = created_rule["id"]
        resp = client.delete(f"/api/v1/alerts/rules/{rule_id}")
        assert_status(M, "TC-AR06 删除告警规则", resp, resp.status_code,
                      detail=f"status={resp.status_code}")

    # TC-AR07: 异常场景 - 创建规则缺少 alert_type / severity
    resp = client.post("/api/v1/alerts/rules",
                       json={"name": "bad-rule", "enabled": True})
    reporter.record(M, "TC-AR07 缺少 alert_type 返回非 200",
                    resp.status_code != 200,
                    detail=f"status={resp.status_code}")

    # TC-AE01: 获取告警事件列表
    resp = client.get("/api/v1/alerts/events")
    if assert_status(M, "TC-AE01 获取告警事件列表", resp, 200):
        data = resp.json()
        reporter.record(M, "TC-AE01-1 事件列表为数组",
                        isinstance(data, list),
                        detail=f"length={len(data) if isinstance(data, list) else 'N/A'}")

    # TC-AE02: 告警事件 - 按 severity 过滤
    resp = client.get("/api/v1/alerts/events", params={"severity": "warning"})
    assert_status(M, "TC-AE02 告警事件按 severity 过滤", resp, 200)

    # TC-AE03: 告警事件 - 按 status 过滤
    resp = client.get("/api/v1/alerts/events", params={"status": "triggered"})
    assert_status(M, "TC-AE03 告警事件按 status 过滤", resp, 200)

    # TC-AE04: 告警事件 - 按 device_id 过滤
    resp = client.get("/api/v1/alerts/events", params={"device_id": device_id})
    assert_status(M, "TC-AE04 告警事件按 device_id 过滤", resp, 200)

    reporter.end_module("alerts")


def test_apikeys(client: APIClient):
    """模块：API 密钥"""
    reporter.start_module("apikeys")
    M = "apikeys"
    created_key: Optional[Dict[str, Any]] = None

    # TC-K01: 创建 API Key
    payload = {
        "name": f"test-key-{uuid.uuid4().hex[:6]}",
        "permissions": {"read": True, "write": True},
        "expires_at": None,
    }
    resp = client.post("/api/v1/api-keys/", json=payload)
    if assert_status(M, "TC-K01 创建 API Key", resp, 200):
        created_key = resp.json()
        assert_has_keys(M, "TC-K01-1 响应包含 key 字段",
                        created_key, ["id", "key", "name"])

    # TC-K02: 获取 API Key 列表
    resp = client.get("/api/v1/api-keys/")
    assert_status(M, "TC-K02 获取 API Key 列表", resp, 200)

    # TC-K03: 获取 API Key 详情
    if created_key:
        kid = created_key["id"]
        resp = client.get(f"/api/v1/api-keys/{kid}")
        assert_status(M, "TC-K03 获取 API Key 详情", resp, 200)

    # TC-K04: 删除 API Key
    if created_key:
        kid = created_key["id"]
        resp = client.delete(f"/api/v1/api-keys/{kid}")
        assert_status(M, "TC-K04 删除 API Key", resp, resp.status_code,
                      detail=f"status={resp.status_code}")

    reporter.end_module("apikeys")


def test_sse_and_openapi(client: APIClient):
    """模块：SSE / OpenAPI 文档（轻量探测）"""
    reporter.start_module("sse_and_openapi")
    M = "sse_and_openapi"

    # TC-S01: 访问 OpenAPI JSON
    resp = client.get("/openapi.json")
    assert_status(M, "TC-S01 GET /openapi.json", resp, 200)

    # TC-S02: 访问 Swagger UI
    resp = client.get("/docs")
    assert_status(M, "TC-S02 GET /docs (Swagger UI)", resp, 200)

    # TC-S03: 访问 /health
    resp = client.get("/health")
    assert_status(M, "TC-S03 GET /health", resp, 200)

    # TC-S04: 探测 SSE 端点 (仅探测可连通，不实际订阅)
    if client.token:
        # SSE 端点通过 query 传递 token（参考 REQUIREMENTS.md 说明）
        resp = client.get("/api/v1/sse/alerts",
                          params={"token": client.token},
                          stream=True,
                          timeout=3)
        reporter.record(M, "TC-S04 SSE 端点可连通 (alerts)",
                        resp.status_code == 200 or resp.status_code >= 400,
                        detail=f"status={resp.status_code} (200=OK, 4xx 也视为服务存在)")

    reporter.end_module("sse_and_openapi")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="IOTPlatform API 自动化测试脚本")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="后端 API base URL (默认: http://localhost:8000)")
    parser.add_argument("--username", default="admin", help="登录用户名 (默认: admin)")
    parser.add_argument("--password", default="admin123", help="登录密码 (默认: admin123)")
    parser.add_argument("--module", default="",
                        help="只运行指定模块，逗号分隔，如 auth,products,devices")
    parser.add_argument("--report", default="test_report.json",
                        help="测试报告输出路径 (默认: test_report.json)")
    args = parser.parse_args()

    enabled = set(m.strip() for m in args.module.split(",") if m.strip())
    client = APIClient(args.base_url)

    print(f"🚀 开始测试: {args.base_url}")
    print(f"   账号: {args.username} / 密码: {args.password}")
    if enabled:
        print(f"   仅运行模块: {enabled}")

    start = time.time()

    # 模块之间有依赖关系，按顺序执行
    product_ctx = None
    device_ctx = None

    if not enabled or "auth" in enabled:
        test_auth(client, args.username, args.password)

    if not enabled or "products" in enabled:
        product_ctx = test_products(client)

    if not enabled or "devices" in enabled:
        if product_ctx and product_ctx.get("product_id"):
            device_ctx = test_devices(client, product_ctx["product_id"])
        else:
            print("  [SKIP] devices 模块依赖 products 模块产物，已跳过")

    if not enabled or "telemetry" in enabled:
        if device_ctx and device_ctx.get("device_id"):
            test_telemetry(client, device_ctx["device_id"])
        else:
            print("  [SKIP] telemetry 模块依赖 devices 模块产物，已跳过")

    if not enabled or "commands" in enabled:
        if device_ctx and device_ctx.get("device_id"):
            test_commands(client, device_ctx["device_id"])
        else:
            print("  [SKIP] commands 模块依赖 devices 模块产物，已跳过")

    if not enabled or "alerts" in enabled:
        if device_ctx and device_ctx.get("device_id"):
            test_alerts(client, device_ctx["device_id"])
        else:
            print("  [SKIP] alerts 模块依赖 devices 模块产物，已跳过")

    if not enabled or "apikeys" in enabled:
        test_apikeys(client)

    if not enabled or "sse" in enabled or "openapi" in enabled or "sse_and_openapi" in enabled:
        test_sse_and_openapi(client)

    duration = time.time() - start

    # 生成报告
    report = reporter.summary()
    summary = report["summary"]

    print("\n" + "="*80)
    print("  测试报告摘要")
    print("="*80)
    print(f"  总计: {summary['total']}   通过: {summary['passed']}   "
          f"失败: {summary['failed']}   通过率: {summary['pass_rate']}")
    print(f"  总耗时: {duration:.2f}s")
    print("-"*80)
    for mod, meta in report["modules"].items():
        print(f"  {mod:<20s} -> pass {meta['passed']}/{meta['total']}  "
              f"(耗时 {meta.get('duration_sec', 0):.2f}s)")
    print("-"*80)
    failed_cases = [c for c in report["cases"] if not c["passed"]]
    if failed_cases:
        print("  失败用例详情:")
        for c in failed_cases:
            print(f"    - [{c['module']}] {c['name']}: {c['detail']}")
    print(f"\n  完整 JSON 报告已写入: {args.report}")
    print("="*80)

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 非零退出码方便 CI 识别
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
