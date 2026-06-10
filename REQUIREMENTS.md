# IOTPlatform 物联网平台需求文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | IOTPlatform |
| 版本 | v1.0 |
| 技术栈 | Vue.js 3 + FastAPI + PostgreSQL + Redis + Mosquitto |
| 部署方式 | Docker Compose |

---

## 一、系统概述

### 1.1 项目背景

IOTPlatform 是一套完整的物联网设备管理平台，提供从设备接入、数据采集到命令下发、告警监控的全链路能力。平台采用前后端分离架构，支持 Docker 一键部署，适用于高校技能大赛教学、实验环境搭建、小型物联网应用开发等场景。

### 1.2 核心功能

| 功能模块 | 功能描述 | 状态 |
|----------|----------|------|
| 用户认证 | 登录、登出、Token 认证 | ✅ |
| 产品管理 | 产品定义、属性/服务/事件管理 | ✅ |
| 设备管理 | 设备注册、密钥管理、状态监控 | ✅ |
| 遥测数据 | 设备上报数据采集与展示 | ✅ |
| 命令下发 | 向设备发送控制命令 | ✅ |
| 告警规则 | 阈值告警、设备上下线告警 | ✅ |
| 告警事件 | 告警事件实时推送与管理 | ✅ |
| API密钥 | 第三方接入密钥管理 | ✅ |
| SSE推送 | 告警/设备状态实时推送 | ✅ |

### 1.3 系统架构

```
┌────────────────────────────────────────────────────────────┐
│ 前端 (Vue.js 3 + Element Plus)                             │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐ │
│  │仪表盘  │  │设备管理│  │命令下发│  │遥测数据│  │告警规则│ │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘ │
└────────────────────────┬───────────────────────────────────┘
                         │ HTTP / SSE
                         ▼
┌────────────────────────────────────────────────────────────┐
│ 后端 (FastAPI + Python 3.10)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │API路由   │  │业务逻辑   │  │MQTT处理  │  │告警引擎   │   │
│  │(devices  │  │(认证/     │  │(消息     │  │(规则匹配/ │   │
│  │ products │  │ 数据校验) │  │ 分发)   │  │ SSE推送) │   │
│  │ alerts)  │  │          │  │         │  │         │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────┬─────────────────┬─────────────────┬───────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ Redis        │  │ Mosquitto    │
│ (关系数据库) │  │ (缓存)        │  │ (MQTT Broker) │
└──────────────┘  └──────────────┘  └──────┬───────┘
                                            │ MQTT
                                            ▼
                                   ┌──────────────────┐
                                   │ 物联网设备       │
                                   │ (传感器/控制器)  │
                                   └──────────────────┘
```

### 1.4 数据流转图

```
设备上报遥测
    │
    ▼
MQTT Topic: devices/{device_key}/telemetry
    │
    ▼
MQTT Handler 解析并验证设备密钥
    │
    ├─ 验证通过 → 更新设备状态为 online → 存储数据到 Telemetry 表
    │                                              │
    │                                              ▼
    │                                       AlertEngine 检查规则
    │                                              │
    │                                              ├─ 触发阈值告警 → 创建 AlertEvent → SSE 推送前端
    │                                              └─ 设备状态变更 → 创建设备状态告警 → SSE 推送前端
    │
    └─ 验证失败 → 记录日志，忽略消息

命令下发流程
    │
    ▼
用户在前端点击"发送命令"
    │
    ▼
后端 API 创建 Command 记录（status: pending）
    │
    ▼
MQTT 发布命令到 devices/{device_key}/commands
    │
    ▼
设备接收命令并执行
    │
    ▼
设备发送响应到 devices/{device_key}/commands/response
    │
    ▼
MQTT Handler 更新 Command 状态（status: executed/failed）
```

---

## 二、功能需求详细设计

### 2.1 用户认证模块

#### 2.1.1 功能描述

提供用户登录、登出功能，采用 JWT Token 认证机制，保护 API 接口安全。

#### 2.1.2 数据模型

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | 用户ID | ✅ |
| username | String(50) | 用户名（唯一） | ✅ |
| email | String(100) | 邮箱 | ❌ |
| hashed_password | String(255) | 哈希后的密码 | ✅ |
| is_active | Boolean | 是否启用 | ✅ |
| created_at | DateTime | 创建时间 | ✅ |

#### 2.1.3 API 接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/login | 用户登录 | ❌ |
| GET | /api/v1/auth/me | 获取当前用户信息 | ✅ |

#### 2.1.4 前端页面

- 登录页面：用户名/密码输入，登录按钮
- 默认账号：admin / admin123（首次启动自动创建）

#### 2.1.5 关键实现点

- 密码使用 `hashlib.sha256` 加盐哈希存储
- Token 有效期：默认 24 小时
- 前端使用 Pinia 的 `auth.js` 管理 Token 状态
- 路由守卫自动检查认证状态，未登录重定向到登录页

---

### 2.2 产品管理模块

#### 2.2.1 功能描述

产品是设备的"模板"。每个产品定义了该类设备具有的属性（上报的数据）、服务（可下发的命令）和事件（设备主动触发的事件）。

#### 2.2.2 数据模型

**Product 产品**

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| product_key | String(64) | 产品密钥（唯一） | ✅ |
| name | String(100) | 产品名称 | ✅ |
| category | String(50) | 产品类别 | ❌ |
| model | String(50) | 型号 | ❌ |
| manufacturer | String(100) | 制造商 | ❌ |
| description | Text | 描述 | ❌ |
| owner_id | Integer | 所属用户ID | ✅ |

**ProductProperty 产品属性**（设备上报的数据定义）

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| product_id | Integer | 产品ID | ✅ |
| identifier | String(100) | 属性标识符（唯一） | ✅ |
| name | String(100) | 属性显示名称 | ✅ |
| data_type | Enum | 数据类型：string/int/float/bool/date/enum/json | ✅ |
| access_type | Enum | 读写权限：r（只读）/w（只写）/rw（读写） | ✅ |
| unit | String(20) | 单位 | ❌ |
| min_value | Float | 最小值 | ❌ |
| max_value | Float | 最大值 | ❌ |
| default_value | String | 默认值 | ❌ |
| description | Text | 描述 | ❌ |

**ProductService 产品服务**（可下发给设备的命令定义）

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| product_id | Integer | 产品ID | ✅ |
| identifier | String(100) | 服务标识符（唯一） | ✅ |
| name | String(100) | 服务显示名称 | ✅ |
| description | Text | 描述 | ❌ |
| input_params | JSON | 输入参数定义（JSON Schema 格式） | ❌ |
| output_params | JSON | 输出参数定义 | ❌ |

**ProductEvent 产品事件**（设备主动上报的事件定义）

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| product_id | Integer | 产品ID | ✅ |
| identifier | String(100) | 事件标识符（唯一） | ✅ |
| name | String(100) | 事件显示名称 | ✅ |
| event_type | String(50) | 事件类型：info/warning/error | ❌ |
| description | Text | 描述 | ❌ |
| output_params | JSON | 输出参数定义 | ❌ |

#### 2.2.3 API 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/v1/products/ | 创建产品 |
| GET | /api/v1/products/ | 获取产品列表 |
| GET | /api/v1/products/{product_key} | 获取产品详情 |
| PUT | /api/v1/products/{product_key} | 更新产品 |
| DELETE | /api/v1/products/{product_key} | 删除产品 |
| POST | /api/v1/products/{product_key}/properties | 创建属性 |
| GET | /api/v1/products/{product_key}/properties | 获取属性列表 |
| PUT | /api/v1/products/{product_key}/properties/{identifier} | 更新属性 |
| DELETE | /api/v1/products/{product_key}/properties/{identifier} | 删除属性 |
| POST | /api/v1/products/{product_key}/services | 创建服务 |
| GET | /api/v1/products/{product_key}/services | 获取服务列表 |
| PUT | /api/v1/products/{product_key}/services/{identifier} | 更新服务 |
| DELETE | /api/v1/products/{product_key}/services/{identifier} | 删除服务 |
| POST | /api/v1/products/{product_key}/events | 创建事件 |
| GET | /api/v1/products/{product_key}/events | 获取事件列表 |
| PUT | /api/v1/products/{product_key}/events/{identifier} | 更新事件 |
| DELETE | /api/v1/products/{product_key}/events/{identifier} | 删除事件 |

#### 2.2.4 前端页面

- 产品列表页：显示所有产品，支持增删改
- 编辑弹窗：分 Tab 管理基本信息、属性、服务、事件
- 参数输入：支持可视化配置服务的输入参数类型

---

### 2.3 设备管理模块

#### 2.3.1 功能描述

设备是实际连接的终端设备。每个设备属于某个产品，具有自动生成的 device_key 和 device_secret 用于接入认证。

#### 2.3.2 数据模型

**Device 设备**

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| device_key | String(32) | 设备标识（自动生成，唯一） | ✅ |
| device_secret | String(64) | 设备密钥（自动生成） | ✅ |
| device_name | String(100) | 设备显示名称 | ✅ |
| product_id | Integer | 所属产品ID | ✅ |
| status | Enum | 设备状态：online/offline/error | ✅ |
| last_seen | DateTime | 最后一次上报时间 | ❌ |
| status_changed_at | DateTime | 最后一次状态变更时间 | ❌ |
| owner_id | Integer | 所属用户ID | ✅ |
| extra | JSON | 扩展属性 | ❌ |

**Telemetry 遥测数据**

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| device_id | Integer | 设备ID | ✅ |
| property_identifier | String(100) | 对应产品属性标识符 | ✅ |
| value | String | 数据值（字符串存储） | ✅ |
| timestamp | DateTime | 上报时间 | ✅ |
| quality | String(20) | 数据质量：good/bad/uncertain | ❌ |

**Command 命令记录**

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| command_id | String(64) | 命令唯一标识（UUID） | ✅ |
| device_id | Integer | 目标设备ID | ✅ |
| service_identifier | String(100) | 对应服务标识符 | ✅ |
| parameters | JSON | 命令参数 | ✅ |
| status | Enum | 命令状态：pending/executing/executed/failed | ✅ |
| issued_at | DateTime | 下发时间 | ✅ |
| executed_at | DateTime | 执行时间 | ❌ |
| output_data | JSON | 执行结果 | ❌ |
| error_message | Text | 错误信息 | ❌ |

**DeviceEventRecord 设备事件记录**

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| device_id | Integer | 设备ID | ✅ |
| event_identifier | String(100) | 对应产品事件标识符 | ✅ |
| event_data | JSON | 事件数据 | ❌ |
| timestamp | DateTime | 事件时间 | ✅ |

#### 2.3.3 API 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/v1/devices/ | 创建设备 |
| GET | /api/v1/devices/ | 获取设备列表（支持按 product_id/status 过滤） |
| GET | /api/v1/devices/{device_id} | 获取设备详情（含产品定义信息） |
| PUT | /api/v1/devices/{device_id} | 更新设备 |
| DELETE | /api/v1/devices/{device_id} | 删除设备 |
| POST | /api/v1/devices/{device_id}/regenerate-secret | 重新生成设备密钥 |
| GET | /api/v1/telemetry/ | 获取遥测数据（按 device_id/property 过滤） |
| POST | /api/v1/commands/ | 下发命令 |
| GET | /api/v1/commands/ | 获取命令列表 |
| GET | /api/v1/commands/{command_id} | 获取命令详情 |

#### 2.3.4 前端页面

- **设备列表页**：显示所有设备，含在线状态、最后上报时间、复制密钥按钮
- **设备详情页**：显示设备详细信息、属性列表、命令下发功能
- **遥测数据页**：按设备查看历史数据，支持属性筛选和时间范围筛选
- **命令下发页**：选择设备、选择服务、填写参数、执行命令

---

### 2.4 MQTT 消息处理

#### 2.4.1 Topic 规范

所有 MQTT 消息均遵循以下主题规范：

| 主题 (Topic) | 方向 | 说明 |
|--------------|------|------|
| devices/{device_key}/telemetry | 设备 → 平台 | 设备上报遥测数据 |
| devices/{device_key}/status | 设备 → 平台 | 设备上报状态变化 |
| devices/{device_key}/events | 设备 → 平台 | 设备主动上报事件 |
| devices/{device_key}/commands | 平台 → 设备 | 平台下发命令给设备 |
| devices/{device_key}/commands/response | 设备 → 平台 | 设备响应命令执行结果 |

#### 2.4.2 消息格式

**遥测数据上报**

```json
{
  "device_secret": "abc123xyz789",
  "property_identifier": "temperature",
  "value": 25.5,
  "timestamp": "2024-01-01T12:00:00Z",
  "quality": "good"
}
```

**设备状态上报**

```json
{
  "device_secret": "abc123xyz789",
  "status": "online",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**命令下发（平台 → 设备）**

```json
{
  "command_id": "cmd-550e8400-e29b-41d4-a716-446655440000",
  "service_identifier": "set_switch",
  "parameters": {
    "state": true
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**命令响应（设备 → 平台）**

```json
{
  "command_id": "cmd-550e8400-e29b-41d4-a716-446655440000",
  "status": "executed",
  "output_data": {
    "result": "success"
  },
  "timestamp": "2024-01-01T12:00:01Z"
}
```

#### 2.4.3 实现要点

- 使用 `gmqtt` Python 库作为 MQTT 客户端
- MQTT 客户端在应用启动时（`app.startup` 事件）初始化连接
- 所有消息处理在 `backend/app/mqtt/handler.py` 中实现
- 设备密钥验证：每个消息必须包含正确的 device_secret，否则忽略
- 每次收到遥测数据，自动更新设备状态为 online 和 last_seen 时间

---

### 2.5 告警规则模块

#### 2.5.1 功能描述

支持配置告警规则，当设备上报数据满足特定条件时触发告警。

#### 2.5.2 告警类型

| 类型 | 描述 | 示例 |
|------|------|------|
| 阈值告警 | 当某个属性值满足条件时触发 | 温度 > 30°C |
| 设备上下线告警 | 设备从 online → offline 时触发 | 设备离线 |

#### 2.5.3 数据模型

**AlertRule 告警规则**

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| name | String(100) | 规则名称 | ✅ |
| description | Text | 描述 | ❌ |
| alert_type | String(30) | 告警类型：threshold/device_status | ✅ |
| device_id | Integer | 适用设备ID（null 表示所有设备） | ❌ |
| property_identifier | String(100) | 监控的属性标识符（阈值告警必填） | 条件 |
| operator | String(10) | 比较运算符：>/</>=/<=/==/!=（阈值告警必填） | 条件 |
| threshold_value | String | 阈值（阈值告警必填） | 条件 |
| severity | String(20) | 严重级别：info/warning/error/critical | ✅ |
| duration_seconds | Integer | 持续时间（秒），满足条件需持续多久才触发 | ❌ |
| cooldown_seconds | Integer | 冷却时间（秒），同一告警多久内不重复触发 | ❌ |
| silent_from_hour | Integer | 静默开始时间（0-23） | ❌ |
| silent_to_hour | Integer | 静默结束时间（0-23） | ❌ |
| enabled | Boolean | 是否启用 | ✅ |
| owner_id | Integer | 所属用户ID | ✅ |
| last_triggered_at | DateTime | 最后触发时间 | ❌ |
| created_at | DateTime | 创建时间 | ✅ |

**AlertEvent 告警事件**（实际触发的告警记录）

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| rule_id | Integer | 触发的规则ID | ❌ |
| device_id | Integer | 关联设备ID | ✅ |
| message | String(500) | 告警消息 | ✅ |
| severity | String(20) | 严重级别 | ✅ |
| current_value | String | 触发时的当前值 | ❌ |
| threshold_value | String | 触发时的阈值 | ❌ |
| status | String(20) | 状态：triggered/acknowledged/resolved | ✅ |
| acknowledged_at | DateTime | 确认时间 | ❌ |
| resolved_at | DateTime | 解决时间 | ❌ |
| created_at | DateTime | 创建时间 | ✅ |

#### 2.5.4 API 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/v1/alerts/rules | 创建告警规则 |
| GET | /api/v1/alerts/rules | 获取规则列表 |
| GET | /api/v1/alerts/rules/{rule_id} | 获取规则详情 |
| PUT | /api/v1/alerts/rules/{rule_id} | 更新规则 |
| DELETE | /api/v1/alerts/rules/{rule_id} | 删除规则 |
| GET | /api/v1/alerts/events | 获取告警事件列表（支持按 status 过滤） |
| PUT | /api/v1/alerts/events/{event_id}/status | 更新告警事件状态 |

#### 2.5.5 前端页面

- **告警规则页**：规则列表、创建/编辑规则弹窗
- **告警事件页**：实时告警列表，支持确认、标记解决
- **SSE 实时推送**：新告警产生时，前端实时接收并弹出通知

#### 2.5.6 实现要点

- `AlertEngine`（`backend/app/services/alert_service.py`）在每次收到遥测数据或设备状态变更时执行规则检查
- 支持冷却时间避免告警风暴
- 支持静默时段配置（如夜间不触发通知）
- 触发告警后通过 SSE 推送到前端，前端实时显示通知

---

### 2.6 SSE 实时推送模块

#### 2.6.1 功能描述

使用 Server-Sent Events（SSE）技术，将告警事件、设备状态变化实时推送到前端页面。

#### 2.6.2 SSE 端点

| 端点 | 描述 |
|------|------|
| GET /api/v1/sse/alerts | 告警事件推送流 |
| GET /api/v1/sse/devices | 设备状态变化推送流 |

#### 2.6.3 事件格式

**新告警事件** (event: new_alert)

```json
{
  "type": "new_alert",
  "data": {
    "id": 1,
    "message": "设备温度超过阈值: 35°C > 30°C",
    "severity": "warning",
    "device_id": 1,
    "device_name": "环境监测设备",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

**设备状态变化** (event: device_status)

```json
{
  "type": "device_status",
  "data": {
    "device_key": "dev_abc123",
    "device_name": "环境监测设备",
    "status": "online"
  }
}
```

#### 2.6.4 实现要点

- 使用 `fastapi` 的 StreamingResponse 返回 SSE 流
- `SSEService`（`backend/app/services/sse_service.py`）管理所有已连接的客户端
- 支持 Token 验证（通过 query 参数传递）
- 前端使用原生 `EventSource` 对象连接，连接断开自动重连
- 前端在 SSE 连接期间更新页面 UI 状态

---

### 2.7 API 密钥管理模块

#### 2.7.1 功能描述

允许用户创建 API 密钥，用于第三方应用通过 HTTP API 接入平台。

#### 2.7.2 数据模型

**APIKey API密钥**

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | Integer | ID | ✅ |
| key | String(64) | API Key（唯一） | ✅ |
| name | String(100) | 密钥名称 | ✅ |
| permission_level | String(20) | 权限级别：read/write/admin | ✅ |
| owner_id | Integer | 所属用户ID | ✅ |
| created_at | DateTime | 创建时间 | ✅ |
| last_used_at | DateTime | 最后使用时间 | ❌ |
| is_active | Boolean | 是否启用 | ✅ |

#### 2.7.3 使用方式

在 HTTP 请求头中添加：

```
X-API-Key: your-api-key-here
```

---

## 三、前端路由与页面结构

### 3.1 路由配置

```
/login                         → Login.vue       登录页
/dashboard                     → Dashboard.vue    仪表盘（数据总览+图表）
/products                      → Products.vue     产品管理
/devices                       → Devices.vue      设备管理
/telemetry                     → Telemetry.vue    遥测数据
/commands                      → Commands.vue     命令下发
/alert-rules                   → AlertRules.vue   告警规则
/alerts                        → Alerts.vue       告警事件
/api-keys                      → APIKeys.vue      API 密钥
```

### 3.2 前端状态管理（Pinia）

| Store | 路径 | 功能 |
|-------|------|------|
| auth | frontend/src/stores/auth.js | 管理用户登录状态、Token |
| device | frontend/src/stores/device.js | 设备状态管理 |
| product | frontend/src/stores/product.js | 产品状态管理 |

### 3.3 API 调用封装

所有 API 调用统一通过 `frontend/src/services/api.js`：

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器：自动添加 Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401 自动登出
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### 3.4 国际化（i18n）

- 翻译文件位置：`frontend/src/locales/zh.js` 和 `en.js`
- 支持中英文切换（导航栏切换）
- 新增文本时需在两个语言文件中同步添加

---

## 四、后端架构

### 4.1 目录结构

```
backend/app/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置管理
├── database.py             # 数据库连接
├── api/
│   ├── __init__.py
│   ├── devices.py          # 设备 API
│   ├── products.py         # 产品 API
│   ├── telemetry.py        # 遥测数据 API
│   ├── commands.py         # 命令 API
│   ├── alerts.py           # 告警 API
│   ├── apikeys.py          # API 密钥 API
│   ├── sse.py              # SSE 推送 API
│   └── deps.py             # 依赖注入（认证等）
├── models/
│   ├── __init__.py
│   └── models.py           # SQLAlchemy ORM 模型
├── schemas/
│   ├── __init__.py
│   ├── device.py           # 设备 Pydantic Schema
│   ├── product.py          # 产品 Pydantic Schema
│   └── command.py          # 命令 Pydantic Schema
├── security/
│   ├── __init__.py
│   └── auth.py             # JWT 认证
├── services/
│   ├── __init__.py
│   ├── alert_service.py    # 告警引擎
│   ├── init_service.py     # 初始化服务（创建默认用户等）
│   └── sse_service.py      # SSE 推送服务
└── mqtt/
    ├── __init__.py
    ├── service.py          # MQTT 客户端管理
    └── handler.py          # MQTT 消息处理
```

### 4.2 配置环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | postgresql+asyncpg://postgres:postgres@postgres:5432/iot_platform | 数据库连接 |
| REDIS_URL | redis://redis:6379/0 | Redis 连接 |
| MQTT_BROKER_URL | mosquitto | MQTT Broker 地址 |
| MQTT_BROKER_PORT | 1883 | MQTT 端口 |
| SECRET_KEY | your-production-secret-key-change-me-in-production | JWT 签名密钥 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 1440 | Token 有效期（分钟） |

---

## 五、部署配置

### 5.1 Docker Compose 服务清单

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| postgres | postgres:16-alpine | 5432 | 关系数据库 |
| redis | redis:7-alpine | 6379 | 缓存 |
| mosquitto | eclipse-mosquitto | 1883/9001 | MQTT Broker |
| backend | 自定义构建 | 8000 | FastAPI 后端 |
| frontend | 自定义构建 | 3000 | Vue.js 前端（Nginx 托管） |

### 5.2 Dockerfile

**Dockerfile.backend** - 基于 Python 3.10 构建 FastAPI 应用

**Dockerfile.frontend** - 两阶段构建：
1. Node 阶段：npm install && npm run build
2. Nginx 阶段：使用 nginx.conf 托管 dist 目录，同时配置 /api 反向代理到 backend

### 5.3 初始化数据

应用首次启动时，`init_service.py` 会自动：
1. 创建默认管理员账号（username: admin, password: admin123）
2. 初始化数据库表结构（基于 SQLAlchemy models）

---

## 六、非功能需求

### 6.1 性能要求

| 指标 | 目标 |
|------|------|
| API 响应时间 | < 200ms（95%） |
| 设备接入量 | 支持 1000+ 设备同时在线 |
| 遥测数据处理 | 每秒至少 100 条消息 |
| 前端页面加载 | 首屏 < 3s |

### 6.2 安全要求

- 密码必须哈希存储，禁止明文
- 设备接入必须携带 device_secret 验证
- JWT Token 必须有有效期，默认 24 小时
- API 支持基于 API Key 的第三方认证

### 6.3 兼容性要求

- 浏览器：Chrome/Edge/Firefox 最新两个主版本
- 屏幕：支持桌面端自适应（≥ 1024px 宽度）
- Docker：兼容 Docker Compose v2

---

## 七、测试用例清单（供比赛展示使用）

### 7.1 功能测试用例

| # | 测试场景 | 步骤 | 预期结果 |
|---|----------|------|----------|
| TC01 | 用户登录 | 打开登录页 → 输入 admin/admin123 → 点击登录 | 跳转到仪表盘 |
| TC02 | 创建产品 | 进入产品管理 → 新增产品 → 填写信息 → 保存 | 产品列表显示新产品 |
| TC03 | 为产品添加属性 | 编辑产品 → 添加属性（temperature, float, 只读） | 属性列表新增一条 |
| TC04 | 为产品添加服务 | 编辑产品 → 添加服务（set_switch, 布尔参数 state） | 服务列表新增一条 |
| TC05 | 创建设备 | 进入设备管理 → 新增设备 → 关联产品 → 保存 | 生成 device_key 和 device_secret，设备显示在列表中 |
| TC06 | 模拟器上报数据 | 运行模拟器脚本，指定 device_secret | 遥测数据页可看到新数据；设备状态变为 online |
| TC07 | 下发命令 | 进入命令下发 → 选择设备和服务 → 发送命令 | 命令状态变为 executed，模拟器日志显示收到命令 |
| TC08 | 配置阈值告警 | 进入告警规则 → 新建规则：温度 > 30°C 告警 | 规则列表显示新规则 |
| TC09 | 触发告警 | 模拟器发送温度 > 30°C 的数据 | 告警事件页出现新告警，前端弹出通知 |
| TC10 | SSE 实时推送 | 保持告警事件页打开；模拟器发送触发数据 | 页面无需刷新即可看到新告警 |

---

## 八、验收标准

1. ✅ Docker Compose 一键启动，前端在 3000 端口可访问
2. ✅ 能正常登录 admin 账号
3. ✅ 能创建产品、属性、服务
4. ✅ 能创建设备并获取 device_secret
5. ✅ 模拟器能成功连接 MQTT 并上报数据
6. ✅ 遥测数据页能实时看到设备上报数据
7. ✅ 命令能成功下发到设备
8. ✅ 告警规则能正确触发并在前端实时显示
9. ✅ 设备状态变化能实时同步到仪表盘

---

## 附录：API 完整接口列表

可通过以下方式获取 OpenAPI 文档：

- Swagger UI：http://localhost:8000/docs
- JSON 规范：http://localhost:8000/openapi.json

**核心 API 汇总：**

| 模块 | 前缀 | 数量 |
|------|------|------|
| 认证 | /api/v1/auth | 2 |
| 产品 | /api/v1/products | 16 |
| 设备 | /api/v1/devices | 5 |
| 遥测 | /api/v1/telemetry | 3 |
| 命令 | /api/v1/commands | 3 |
| 告警规则 | /api/v1/alerts/rules | 5 |
| 告警事件 | /api/v1/alerts/events | 3 |
| API密钥 | /api/v1/api-keys | 3 |
| SSE | /api/v1/sse | 2 |

**总计：约 42 个 REST API + 2 个 SSE 流式端点**
