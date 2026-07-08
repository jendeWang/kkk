# IoT平台鸿蒙端侧对接文档 v1.0

## 一、概述

本文档描述鸿蒙设备端与IoT平台的对接方式，包括MQTT通信协议、消息格式、主题规范等。

**平台架构：**
- 后端：FastAPI + SQLAlchemy (异步)
- MQTT Broker：Mosquitto (支持用户名/密码认证)
- 数据协议：JSON over MQTT

---

## 二、MQTT连接信息

| 项 | 值 | 说明 |
|---|---|---|
| Broker地址 | 实际部署的服务器IP/域名 | 云端环境：`localhost` |
| 端口 | `1883` | MQTT标准端口 |
| 认证方式 | 用户名/密码 | 需联系管理员分配MQTT凭证 |
| Client ID | 建议使用 `device-{device_key}` | 全局唯一 |
| KeepAlive | `60`秒 | 心跳间隔 |
| QoS | `1` (至少一次) | 建议使用 |

**连接示例（Python）：**
```python
import paho.mqtt.client as mqtt

client = mqtt.Client(client_id=f"device-{device_key}")
client.username_pw_set(username, password)
client.connect(broker_url, 1883, 60)
```

---

## 三、设备身份凭证

每台设备在平台注册后获得以下凭证：

| 字段 | 长度 | 说明 |
|---|---|---|
| `device_key` | 32位 | 设备唯一标识，用于MQTT主题 |
| `device_secret` | 64位 | 设备密钥，用于消息认证 |

> **安全说明：** `device_secret` 应安全存储在设备端，建议写入消息体进行身份验证。

---

## 四、MQTT主题规范

### 4.1 设备 → 平台（上报）

| 主题 | 用途 | QoS |
|---|---|---|
| `devices/{device_key}/telemetry` | 遥测数据上报 | 1 |
| `devices/{device_key}/status` | 设备上下线状态 | 1 |
| `devices/{device_key}/events` | 设备事件上报 | 1 |
| `devices/{device_key}/commands/response` | 命令执行结果回传 | 1 |
| `devices/{device_key}/shadow/update` | 设备影子上报（reported） | 1 |

### 4.2 平台 → 设备（下发）

| 主题 | 用途 | QoS |
|---|---|---|
| `devices/{device_key}/commands` | 平台下发命令 | 1 |
| `devices/{device_key}/shadow/get/response` | 设备影子查询响应 | 1 |
| `devices/{device_key}/shadow/update/desired` | 期望属性变更通知 | 1 |

> **设备端需订阅：** `devices/{device_key}/commands` 及相关下行主题

---

## 五、消息格式详解

### 5.1 遥测数据上报

**主题：** `devices/{device_key}/telemetry`

**消息体：**
```json
{
  "device_secret": "abc123...",
  "property_identifier": "temperature",
  "value": "25.6",
  "timestamp": "2024-01-15T10:30:00Z",
  "quality": "good"
}
```

| 字段 | 必选 | 类型 | 说明 |
|---|---|---|---|
| `device_secret` | 推荐 | string | 设备密钥，用于身份验证 |
| `property_identifier` | 是 | string | 属性标识符，对应产品物模型定义 |
| `value` | 是 | string | 属性值（统一字符串传输，平台根据类型解析） |
| `timestamp` | 否 | string | ISO8601格式时间戳，缺省则使用服务端时间 |
| `quality` | 否 | string | 数据质量，默认 `good` |

**说明：**
- 每次上报一个属性点
- 上报成功后平台自动将设备置为 `online` 状态
- 平台会根据告警规则自动检测阈值触发告警

---

### 5.2 设备状态上报

**主题：** `devices/{device_key}/status`

**消息体：**
```json
{
  "device_secret": "abc123...",
  "status": "online"
}
```

| 字段 | 必选 | 类型 | 可选值 |
|---|---|---|---|
| `device_secret` | 推荐 | string | 设备密钥 |
| `status` | 是 | string | `online` / `offline` / `error` |

**使用场景：**
- 设备上线时主动上报 `online`
- 设备正常离线前上报 `offline`
- 设备异常时上报 `error`

> 平台也会根据遥测数据自动更新在线状态（最后上报时间超过阈值判定离线）

---

### 5.3 事件上报

**主题：** `devices/{device_key}/events`

**消息体：**
```json
{
  "device_secret": "abc123...",
  "event_identifier": "door_opened",
  "event_data": {
    "door_id": 1,
    "from": "user_a"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

| 字段 | 必选 | 类型 | 说明 |
|---|---|---|---|
| `device_secret` | 推荐 | string | 设备密钥 |
| `event_identifier` | 是 | string | 事件标识符，对应产品物模型 |
| `event_data` | 否 | object | 事件附加数据 |
| `timestamp` | 否 | string | ISO8601时间戳 |

---

### 5.4 命令接收（平台→设备）

**主题：** `devices/{device_key}/commands`

**消息体：**
```json
{
  "command_id": "cmd_abc123xyz",
  "service_identifier": "set_light",
  "input_params": {
    "brightness": 80,
    "mode": "warm"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

| 字段 | 必选 | 类型 | 说明 |
|---|---|---|---|
| `command_id` | 是 | string | 命令唯一ID，回传结果时必须带回 |
| `service_identifier` | 是 | string | 服务标识符，对应产品物模型定义 |
| `input_params` | 是 | object | 命令输入参数 |
| `timestamp` | 是 | string | 命令下发时间 |

**设备端处理流程：**
1. 收到命令后，记录 `command_id`
2. 解析 `service_identifier` 执行对应操作
3. 执行完成后通过 `commands/response` 回传结果

---

### 5.5 命令结果回传（设备→平台）

**主题：** `devices/{device_key}/commands/response`

**成功响应：**
```json
{
  "device_secret": "abc123...",
  "command_id": "cmd_abc123xyz",
  "status": "executed",
  "output_data": {
    "result": "success",
    "current_brightness": 80
  }
}
```

**失败响应：**
```json
{
  "device_secret": "abc123...",
  "command_id": "cmd_abc123xyz",
  "status": "failed",
  "error_message": "Device busy, please try again later"
}
```

| 字段 | 必选 | 类型 | 说明 |
|---|---|---|---|
| `device_secret` | 推荐 | string | 设备密钥 |
| `command_id` | 是 | string | 与收到的命令ID一致 |
| `status` | 是 | string | `executed` / `failed` |
| `output_data` | 否 | object | 执行成功的输出数据 |
| `error_message` | 否 | string | 失败时的错误信息 |

---

### 5.6 设备影子（Device Shadow）

设备影子用于存储设备的当前状态（reported）和期望状态（desired），即使设备离线也能通过影子获取/设置状态。

#### 5.6.1 上报设备影子（reported）

**主题：** `devices/{device_key}/shadow/update`

**消息体：**
```json
{
  "device_secret": "abc123...",
  "state": {
    "reported": {
      "temperature": 25.6,
      "humidity": 65,
      "light_status": "on"
    }
  },
  "version": 1
}
```

#### 5.6.2 获取设备影子

设备主动请求获取完整影子：

**请求主题：** `devices/{device_key}/shadow/get`
```json
{
  "device_secret": "abc123...",
  "token": "req_001"
}
```

**响应主题：** `devices/{device_key}/shadow/get/response`
```json
{
  "token": "req_001",
  "state": {
    "reported": { "temperature": 25.6 },
    "desired": { "light_status": "on" }
  },
  "version": 5,
  "metadata": {
    "reported": { "temperature": { "timestamp": "..." } },
    "desired": { "light_status": { "timestamp": "..." } }
  }
}
```

#### 5.6.3 期望属性变更通知

平台端修改期望属性后，设备会收到通知：

**主题：** `devices/{device_key}/shadow/update/desired`
```json
{
  "state": {
    "desired": {
      "light_status": "on",
      "brightness": 80
    }
  },
  "version": 6
}
```

设备收到后应：
1. 应用 `desired` 中的配置
2. 将结果同步到 `reported`
3. 上报更新后的 `reported` 状态

---

## 六、REST API（可选）

设备端也可通过REST API进行管理操作，使用 **API Key** 认证。

### 认证方式

在请求Header中添加：
```
Authorization: Bearer {api_key}
```

SSE长连接场景也支持通过URL参数：
```
/api/v1/sse/events?api_key={api_key}
```

### 常用API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/v1/devices` | 获取设备列表 |
| `GET` | `/api/v1/devices/{device_key}` | 获取设备详情 |
| `GET` | `/api/v1/devices/{device_key}/telemetry` | 获取遥测历史 |
| `POST` | `/api/v1/commands` | 发送命令 |
| `GET` | `/api/v1/products/{product_key}/tsl` | 获取产品TSL物模型 |
| `GET` | `/api/v1/sse/events` | SSE实时事件订阅 |

### SSE事件订阅

用于实时接收平台推送的告警、设备状态变更等：

```
GET /api/v1/sse/events?api_key={api_key}
Accept: text/event-stream
```

事件类型：
- `device_status` - 设备上下线
- `telemetry` - 遥测数据更新
- `alert` - 告警触发
- `command_response` - 命令响应

---

## 七、智慧大棚物模型参考

### 传感器类属性（只读）

| identifier | 名称 | 类型 | 单位 | 范围 |
|---|---|---|---|---|
| `temperature` | 空气温度 | float | ℃ | -40 ~ 85 |
| `humidity` | 空气湿度 | float | %RH | 0 ~ 100 |
| `light_intensity` | 光照强度 | float | lux | 0 ~ 100000 |
| `soil_moisture` | 土壤湿度 | float | % | 0 ~ 100 |
| `co2` | CO₂浓度 | float | ppm | 0 ~ 5000 |
| `soil_temperature` | 土壤温度 | float | ℃ | -20 ~ 60 |

### 执行器类属性（读写）

| identifier | 名称 | 类型 | 说明 |
|---|---|---|---|
| `fan_status` | 通风扇状态 | bool | true=开, false=关 |
| `light_status` | 补光灯状态 | bool | true=开, false=关 |
| `pump_status` | 灌溉水泵状态 | bool | true=开, false=关 |
| `brightness` | 补光灯亮度 | int | 0-100 |

### 服务（命令）

| identifier | 名称 | 输入参数 |
|---|---|---|
| `set_fan` | 设置通风扇 | `status: bool` |
| `set_light` | 设置补光灯 | `status: bool, brightness: int` |
| `set_pump` | 设置灌溉泵 | `status: bool, duration: int` |
| `set_mode` | 设置工作模式 | `mode: enum[manual/auto]` |
| `raw_command` | 自定义命令 | `data: object` |

### 事件

| identifier | 名称 | 类型 |
|---|---|---|
| `water_shortage` | 缺水告警 | alert |
| `sensor_error` | 传感器故障 | error |
| `task_complete` | 任务完成 | info |

---

## 八、设备端开发建议

### 8.1 连接流程

```
启动 → 连接MQTT → 订阅commands主题 → 上报online状态
→ 循环上报遥测数据(5s/30s/60s间隔)
→ 监听命令并响应
→ 异常重连机制
```

### 8.2 重连策略

```python
# 指数退避重连
delay = 1
while True:
    try:
        client.connect(broker, port)
        delay = 1
        break
    except:
        time.sleep(delay)
        delay = min(delay * 2, 60)  # 最大60秒
```

### 8.3 离线缓存

网络异常时，将遥测数据缓存到本地，恢复连接后批量上报。

### 8.4 消息QoS建议

- 遥测数据：QoS 0 或 QoS 1（根据重要性）
- 状态上报：QoS 1
- 命令响应：QoS 1
- 事件上报：QoS 1

---

## 九、调试工具

### 平台Swagger文档
```
http://{host}:8000/docs
```

### MQTT调试
使用 `mosquitto_sub` / `mosquitto_pub` 或 MQTTX 工具测试：

```bash
# 订阅设备命令
mosquitto_sub -h localhost -p 1883 -u user -P pass -t "devices/+/commands" -v

# 模拟上报遥测
mosquitto_pub -h localhost -p 1883 -u user -P pass \
  -t "devices/dev123/telemetry" \
  -m '{"property_identifier":"temperature","value":"25.6"}'
```

---

## 十、版本历史

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2024-01-15 | 初版，包含MQTT基础通信、遥测、命令、事件、设备影子 |

