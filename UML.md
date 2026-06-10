# IOTPlatform 物联网平台 UML 设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | IOTPlatform |
| 版本 | v1.0 |
| UML 工具 | Mermaid / PlantUML（可在任意支持 Markdown 的编辑器中渲染） |

---

## 一、类图 (Class Diagram) - 数据库实体关系

### 1.1 枚举类型

```mermaid
classDiagram
    class DeviceStatus {
        <<enumeration>>
        ONLINE
        OFFLINE
        ERROR
    }

    class AlertSeverity {
        <<enumeration>>
        INFO
        WARNING
        ERROR
        CRITICAL
    }

    class AlertStatus {
        <<enumeration>>
        TRIGGERED
        ACKNOWLEDGED
        IN_PROGRESS
        RESOLVED
        ARCHIVED
    }

    class AlertType {
        <<enumeration>>
        THRESHOLD
        DEVICE_OFFLINE
        DEVICE_ONLINE
        EVENT
        CUSTOM
    }

    class ConditionOperator {
        <<enumeration>>
        GT
        GTE
        LT
        LTE
        EQ
        NEQ
        INCREASE_RATE
        DECREASE_RATE
    }

    class PropertyDataType {
        <<enumeration>>
        INT
        FLOAT
        BOOL
        STRING
        ENUM
    }

    class PropertyAccessType {
        <<enumeration>>
        READ_ONLY
        READ_WRITE
    }

    class CommandStatus {
        <<enumeration>>
        PENDING
        SENT
        EXECUTED
        FAILED
    }
```

### 1.2 核心实体类图

```mermaid
classDiagram
    direction LR

    class User {
        +Integer id
        +String username
        +String email
        +String hashed_password
        +String full_name
        +Boolean is_active
        +Boolean is_superuser
        +DateTime created_at
        +DateTime updated_at
    }

    class Product {
        +Integer id
        +String product_key
        +String name
        +String category
        +String model
        +String manufacturer
        +String description
        +Integer owner_id
        +DateTime created_at
        +DateTime updated_at
    }

    class ProductProperty {
        +Integer id
        +String identifier
        +String name
        +PropertyDataType data_type
        +PropertyAccessType access_type
        +String unit
        +String min_value
        +String max_value
        +JSON enum_values
        +String default_value
        +String description
        +Integer product_id
        +DateTime created_at
    }

    class ProductService {
        +Integer id
        +String identifier
        +String name
        +String description
        +JSON input_params
        +JSON output_params
        +Integer product_id
        +DateTime created_at
    }

    class ProductEvent {
        +Integer id
        +String identifier
        +String name
        +String event_type
        +String description
        +JSON output_params
        +Integer product_id
        +DateTime created_at
    }

    class Device {
        +Integer id
        +String device_name
        +String device_key
        +String device_secret
        +Integer product_id
        +Integer owner_id
        +DeviceStatus status
        +DateTime last_seen
        +DateTime status_changed_at
        +JSON extra
        +DateTime created_at
        +DateTime updated_at
    }

    class Telemetry {
        +Integer id
        +Integer device_id
        +String property_identifier
        +String value
        +DateTime timestamp
        +String quality
    }

    class DeviceEventRecord {
        +Integer id
        +Integer device_id
        +String event_identifier
        +JSON event_data
        +DateTime timestamp
    }

    class Command {
        +Integer id
        +String command_id
        +Integer device_id
        +String service_identifier
        +JSON input_params
        +CommandStatus status
        +String error_message
        +JSON output_data
        +Integer owner_id
        +DateTime created_at
        +DateTime sent_at
        +DateTime executed_at
    }

    class AlertRule {
        +Integer id
        +String name
        +String description
        +AlertType alert_type
        +Integer product_id
        +Integer device_id
        +String property_identifier
        +ConditionOperator operator
        +String threshold_value
        +Integer duration_seconds
        +Integer delay_seconds
        +AlertSeverity severity
        +Integer cooldown_seconds
        +Boolean enabled
        +Integer silent_from_hour
        +Integer silent_to_hour
        +JSON notification_config
        +Integer owner_id
        +DateTime created_at
        +DateTime updated_at
    }

    class AlertEvent {
        +Integer id
        +Integer rule_id
        +Integer product_id
        +Integer device_id
        +String property_identifier
        +String message
        +AlertSeverity severity
        +AlertStatus status
        +String current_value
        +String threshold_value
        +String operator
        +DateTime acknowledged_at
        +Integer acknowledged_by
        +DateTime resolved_at
        +Integer resolved_by
        +String resolution_notes
        +DateTime created_at
        +DateTime updated_at
    }

    class APIKey {
        +Integer id
        +String key
        +String name
        +Integer user_id
        +JSON permissions
        +DateTime expires_at
        +DateTime last_used
        +Boolean is_active
        +DateTime created_at
    }

    %% 关系
    User "1" -- "0..*" Product : 拥有
    User "1" -- "0..*" Device : 拥有
    User "1" -- "0..*" APIKey : 拥有

    Product "1" -- "0..*" ProductProperty : 包含
    Product "1" -- "0..*" ProductService : 包含
    Product "1" -- "0..*" ProductEvent : 包含
    Product "1" -- "0..*" Device : 包含

    Device "1" -- "0..*" Telemetry : 产生
    Device "1" -- "0..*" DeviceEventRecord : 产生
    Device "1" -- "0..*" Command : 接收

    AlertRule "1" -- "0..*" AlertEvent : 触发
    AlertRule --> Product : 关联
    AlertRule --> Device : 关联
    AlertEvent --> Product : 关联
    AlertEvent --> Device : 关联
    AlertEvent --> User : 确认/解决
```

### 1.3 数据库关系 ER 图

```mermaid
erDiagram
    users ||--o{ products : "owns"
    users ||--o{ devices : "owns"
    users ||--o{ api_keys : "has"
    users ||--o{ alert_events : "acknowledges"

    products ||--o{ product_properties : "has"
    products ||--o{ product_services : "has"
    products ||--o{ product_events : "has"
    products ||--o{ devices : "has instances"
    products ||--o{ alert_rules : "monitored by"
    products ||--o{ alert_events : "related to"

    devices ||--o{ telemetry : "produces"
    devices ||--o{ device_event_records : "produces"
    devices ||--o{ commands : "receives"
    devices ||--o{ alert_rules : "monitored by"
    devices ||--o{ alert_events : "related to"

    alert_rules ||--o{ alert_events : "triggers"

    users {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        boolean is_superuser
        datetime created_at
        datetime updated_at
    }

    products {
        int id PK
        string product_key UK
        string name
        string category
        string model
        string manufacturer
        text description
        int owner_id FK
        datetime created_at
        datetime updated_at
    }

    product_properties {
        int id PK
        string identifier
        string name
        enum data_type
        enum access_type
        string unit
        string min_value
        string max_value
        json enum_values
        string default_value
        text description
        int product_id FK
        datetime created_at
    }

    product_services {
        int id PK
        string identifier
        string name
        text description
        json input_params
        json output_params
        int product_id FK
        datetime created_at
    }

    product_events {
        int id PK
        string identifier
        string name
        string event_type
        text description
        json output_params
        int product_id FK
        datetime created_at
    }

    devices {
        int id PK
        string device_name
        string device_key UK
        string device_secret UK
        int product_id FK
        int owner_id FK
        enum status
        datetime last_seen
        datetime status_changed_at
        json extra
        datetime created_at
        datetime updated_at
    }

    telemetry {
        int id PK
        int device_id FK
        string property_identifier
        string value
        datetime timestamp
        string quality
    }

    device_event_records {
        int id PK
        int device_id FK
        string event_identifier
        json event_data
        datetime timestamp
    }

    commands {
        int id PK
        string command_id UK
        int device_id FK
        string service_identifier
        json input_params
        enum status
        text error_message
        json output_data
        int owner_id FK
        datetime created_at
        datetime sent_at
        datetime executed_at
    }

    alert_rules {
        int id PK
        string name
        text description
        enum alert_type
        int product_id FK
        int device_id FK
        string property_identifier
        enum operator
        string threshold_value
        int duration_seconds
        int delay_seconds
        enum severity
        int cooldown_seconds
        boolean enabled
        int silent_from_hour
        int silent_to_hour
        json notification_config
        int owner_id FK
        datetime created_at
        datetime updated_at
    }

    alert_events {
        int id PK
        int rule_id FK
        int product_id FK
        int device_id FK
        string property_identifier
        text message
        enum severity
        enum status
        string current_value
        string threshold_value
        string operator
        datetime acknowledged_at
        int acknowledged_by FK
        datetime resolved_at
        int resolved_by FK
        text resolution_notes
        datetime created_at
        datetime updated_at
    }

    api_keys {
        int id PK
        string key UK
        string name
        int user_id FK
        json permissions
        datetime expires_at
        datetime last_used
        boolean is_active
        datetime created_at
    }
```

---

## 二、用例图 (Use Case Diagram)

```mermaid
usecaseDiagram
    actor User as "用户"
    actor Device as "设备/模拟器"
    actor ThirdParty as "第三方应用"

    package "用户认证" {
        usecase UC1 as "登录"
        usecase UC2 as "获取当前用户信息"
    }

    package "产品管理" {
        usecase UC3 as "创建产品"
        usecase UC4 as "查看产品列表"
        usecase UC5 as "编辑产品"
        usecase UC6 as "删除产品"
        usecase UC7 as "管理产品属性"
        usecase UC8 as "管理产品服务"
        usecase UC9 as "管理产品事件"
    }

    package "设备管理" {
        usecase UC10 as "创建设备"
        usecase UC11 as "查看设备列表"
        usecase UC12 as "查看设备详情"
        usecase UC13 as "编辑设备"
        usecase UC14 as "删除设备"
        usecase UC15 as "重新生成设备密钥"
    }

    package "遥测数据" {
        usecase UC16 as "查看遥测数据"
        usecase UC17 as "按设备/属性筛选"
        usecase UC18 as "上报遥测数据"
    }

    package "命令下发" {
        usecase UC19 as "发送命令"
        usecase UC20 as "查看命令历史"
        usecase UC21 as "接收命令并执行"
        usecase UC22 as "上报命令执行结果"
    }

    package "告警管理" {
        usecase UC23 as "创建告警规则"
        usecase UC24 as "管理告警规则"
        usecase UC25 as "查看告警事件"
        usecase UC26 as "确认告警"
        usecase UC27 as "标记告警已解决"
        usecase UC28 as "实时接收告警推送"
    }

    package "API 管理" {
        usecase UC29 as "创建 API 密钥"
        usecase UC30 as "管理 API 密钥"
        usecase UC31 as "通过 API Key 访问接口"
    }

    package "仪表盘" {
        usecase UC32 as "查看设备状态总览"
        usecase UC33 as "查看数据统计图表"
    }

    %% 用户用例
    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    User --> UC7
    User --> UC8
    User --> UC9
    User --> UC10
    User --> UC11
    User --> UC12
    User --> UC13
    User --> UC14
    User --> UC15
    User --> UC16
    User --> UC17
    User --> UC19
    User --> UC20
    User --> UC23
    User --> UC24
    User --> UC25
    User --> UC26
    User --> UC27
    User --> UC28
    User --> UC29
    User --> UC30
    User --> UC32
    User --> UC33

    %% 设备用例
    Device --> UC18
    Device --> UC21
    Device --> UC22

    %% 第三方应用用例
    ThirdParty --> UC31
```

---

## 三、时序图 (Sequence Diagram)

### 3.1 用户登录流程

```mermaid
sequenceDiagram
    participant Browser as 浏览器/前端
    participant Backend as FastAPI 后端
    participant DB as PostgreSQL

    Browser->>Backend: POST /api/v1/auth/login<br/>(username, password)
    Backend->>DB: SELECT * FROM users<br/>WHERE username = ?
    DB-->>Backend: 返回用户记录
    alt 用户名或密码错误
        Backend-->>Browser: 401 Unauthorized<br/>{"detail": "Invalid credentials"}
    else 验证通过
        Backend->>Backend: 生成 JWT Token<br/>(payload: user_id, exp)
        Backend-->>Browser: 200 OK<br/>{"access_token": "...", "token_type": "bearer"}
        Browser->>Browser: 保存 Token 到 localStorage
        Browser->>Browser: 跳转至 /dashboard
    end

    Note over Browser,DB: 后续请求都携带 Authorization: Bearer {token}
```

### 3.2 设备上报遥测数据 + 触发告警

```mermaid
sequenceDiagram
    participant Device as 设备/模拟器
    participant MQTT as Mosquitto Broker
    participant Handler as MQTT Handler
    participant DB as PostgreSQL
    participant AlertEngine as AlertEngine
    participant SSE as SSE Service
    participant Browser as 前端浏览器

    Device->>MQTT: PUBLISH<br/>topic: devices/{device_key}/telemetry<br/>payload: {device_secret, property_identifier, value}
    MQTT->>Handler: 转发消息

    Handler->>DB: SELECT * FROM devices WHERE device_key = ?
    DB-->>Handler: 返回设备信息

    alt device_secret 验证失败
        Handler->>Handler: 记录警告日志，忽略消息
    else 验证通过
        Handler->>DB: UPDATE devices SET status=ONLINE, last_seen=now()<br/>INSERT INTO telemetry (device_id, property_identifier, value, ...)
        DB-->>Handler: 保存成功

        Handler->>AlertEngine: process_telemetry(telemetry, device)
        AlertEngine->>DB: SELECT * FROM alert_rules<br/>WHERE property_identifier = ? AND enabled = true
        DB-->>AlertEngine: 返回匹配的告警规则

        loop 每条规则检查
            AlertEngine->>AlertEngine: 比较 value 与 threshold_value<br/>(检查冷却时间、静默时段)
            alt 满足告警条件
                AlertEngine->>DB: INSERT INTO alert_events (...)
                AlertEngine->>SSE: broadcast_event(new_alert_event)
                SSE-->>Browser: SSE Event: new_alert<br/>{message, severity, device_name, ...}
                Browser->>Browser: 弹出通知，更新告警列表
            end
        end

        opt 设备状态从 OFFLINE → ONLINE
            Handler->>AlertEngine: check_device_status(device)
            AlertEngine->>DB: 检查 DEVICE_ONLINE 规则
            alt 存在设备上线告警规则且已启用
                AlertEngine->>DB: INSERT INTO alert_events (...)
                AlertEngine->>SSE: broadcast_event(alert)
            end
        end
    end
```

### 3.3 命令下发流程

```mermaid
sequenceDiagram
    participant Browser as 前端浏览器
    participant Backend as FastAPI 后端
    participant DB as PostgreSQL
    participant MQTT as Mosquitto Broker
    participant Device as 设备

    Browser->>Backend: POST /api/v1/commands<br/>(device_id, service_identifier, parameters)
    Backend->>DB: INSERT INTO commands (command_id, device_id, service_identifier, input_params, status=PENDING, ...)
    DB-->>Backend: 命令记录创建成功

    Backend->>MQTT: PUBLISH<br/>topic: devices/{device_key}/commands<br/>payload: {command_id, service_identifier, parameters, timestamp}
    MQTT-->>Device: 消息投递

    Backend->>DB: UPDATE commands SET status=SENT, sent_at=now()

    opt 设备处理命令
        Device->>Device: 执行命令（如：切换开关、调节亮度）
        Device->>MQTT: PUBLISH<br/>topic: devices/{device_key}/commands/response<br/>payload: {command_id, status="executed", output_data}
        MQTT->>Backend: MQTT Handler 收到响应

        Backend->>DB: UPDATE commands SET status=EXECUTED, executed_at=now(), output_data=?
    end

    Browser->>Backend: GET /api/v1/commands（轮询查询状态）
    Backend->>DB: SELECT * FROM commands WHERE device_id = ? ORDER BY created_at DESC
    DB-->>Backend: 返回命令列表
    Backend-->>Browser: 200 OK [命令列表，含执行状态]
```

### 3.4 SSE 实时推送连接流程

```mermaid
sequenceDiagram
    participant Browser as 前端浏览器
    participant Backend as FastAPI 后端
    participant SSE as SSE Service
    participant AlertEngine as AlertEngine

    Note over Browser,AlertEngine: 页面加载时建立 SSE 连接

    Browser->>Backend: GET /api/v1/sse/alerts?token={jwt_token}<br/>(Accept: text/event-stream)
    Backend->>Backend: 验证 JWT Token
    alt Token 无效
        Backend-->>Browser: 401 Unauthorized
    else Token 有效
        Backend->>SSE: 注册新客户端连接
        SSE-->>Browser: HTTP 200, Content-Type: text/event-stream<br/>Connection: keep-alive
        Browser->>Browser: 创建 EventSource 对象，保持长连接

        loop 持续推送
            Note over AlertEngine,SSE: 有新告警触发时
            AlertEngine->>SSE: broadcast_event(alert_data)
            SSE-->>Browser: SSE 事件推送<br/>event: new_alert<br/>data: {id, message, severity, ...}
            Browser->>Browser: 触发事件回调<br/>→ 更新告警列表、弹出通知
        end

        Note over Browser,SSE: 连接断开时
        Browser->>Browser: EventSource 自动重连
        Browser->>Backend: 重新发起连接请求
    end
```

---

## 四、组件图 (Component Diagram)

### 4.1 后端内部组件

```mermaid
flowchart TB
    subgraph Frontend ["前端 (Vue.js 3)"]
        direction LR
        F1[仪表盘页面]
        F2[产品管理页面]
        F3[设备管理页面]
        F4[命令下发页面]
        F5[遥测数据页面]
        F6[告警规则页面]
        F7[告警事件页面]
        F8[API密钥管理页面]
        F9[Pinia 状态管理]
        F10[i18n 国际化]
        F11[Axios API 封装]
        F12[SSE EventSource]
    end

    subgraph Backend ["后端 (FastAPI)"]
        direction TB
        B1[API 路由层<br/>devices / products / commands / telemetry / alerts / sse]
        B2[认证模块<br/>JWT Token / API Key]
        B3[MQTT 客户端<br/>gmqtt]
        B4[MQTT 消息处理器<br/>handler.py]
        B5[告警引擎<br/>alert_service.py]
        B6[SSE 推送服务<br/>sse_service.py]
        B7[初始化服务<br/>init_service.py]
    end

    subgraph Data ["数据层"]
        direction LR
        D1[(PostgreSQL)]
        D2[(Redis)]
        D3[(Mosquitto MQTT)]
    end

    subgraph DeviceLayer ["设备层"]
        direction LR
        DEV1[物联网设备]
        DEV2[模拟器脚本]
    end

    F11 --> B1
    F12 --> B6
    F1 --> F11
    F2 --> F11
    F3 --> F11
    F4 --> F11
    F5 --> F11
    F6 --> F11
    F7 --> F11 & F12
    F8 --> F11

    B1 --> B2
    B1 --> D1
    B1 --> B5
    B1 --> B6

    B3 --> D3
    B3 --> B4
    B4 --> D1
    B4 --> B5
    B5 --> B6
    B5 --> D1
    B6 -. SSE推送 .-> F12
    B7 --> D1

    DEV1 -- MQTT --> D3
    DEV2 -- MQTT --> D3
    D3 -- MQTT --> DEV1
    D3 -- MQTT --> DEV2

    B2 --> D1
    B1 -. 使用 .-> D2
```

### 4.2 API 模块依赖图

```mermaid
flowchart TD
    A[FastAPI Application<br/>main.py]
    B[API 路由集合<br/>api/__init__.py]

    C1[设备 API<br/>devices.py]
    C2[产品 API<br/>products.py]
    C3[命令 API<br/>commands.py]
    C4[遥测 API<br/>telemetry.py]
    C5[告警 API<br/>alerts.py]
    C6[SSE API<br/>sse.py]
    C7[API密钥 API<br/>apikeys.py]

    D[依赖注入<br/>deps.py]
    E[认证模块<br/>security/auth.py]
    F[数据库<br/>database.py]
    G[ORM 模型<br/>models/models.py]
    H[Pydantic Schemas<br/>schemas/*.py]
    I[服务层<br/>services/*.py]

    A --> B
    B --> C1
    B --> C2
    B --> C3
    B --> C4
    B --> C5
    B --> C6
    B --> C7

    C1 --> D
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C6 --> D
    C7 --> D

    D --> E
    D --> F
    D --> G
    D --> H

    C1 --> G
    C2 --> G
    C3 --> G
    C5 --> I
    C6 --> I
```

---

## 五、部署图 (Deployment Diagram)

### 5.1 Docker Compose 部署架构

```mermaid
flowchart LR
    subgraph Host ["宿主机 (Ubuntu 20.04)"]
        subgraph Docker ["Docker Compose"]
            direction LR

            subgraph FrontendNode ["frontend 容器"]
                FE1[Nginx Server :80]
                FE2[静态资源 dist/]
                FE3[反向代理 /api → backend:8000]
            end

            subgraph BackendNode ["backend 容器"]
                BE1[Uvicorn/FastAPI :8000]
                BE2[MQTT Client]
                BE3[AlertEngine]
                BE4[SSEService]
            end

            subgraph DBNode ["postgres 容器"]
                PG1[(PostgreSQL<br/>:5432)]
            end

            subgraph RedisNode ["redis 容器"]
                RD1[(Redis<br/>:6379)]
            end

            subgraph MQTTNode ["mosquitto 容器"]
                MQ1[Mosquitto Broker<br/>:1883 :9001]
            end
        end

        subgraph Devices ["外部设备"]
            DEV[物联网设备 / 模拟器]
        end
    end

    USER[用户浏览器] -- HTTP :3000 --> FE1
    FE1 -- HTTP :8000 --> BE1

    BE1 -- PostgreSQL :5432 --> PG1
    BE1 -- Redis :6379 --> RD1
    BE2 -- MQTT :1883 --> MQ1

    DEV -- MQTT Publish/Subscribe :1883 --> MQ1
    MQ1 -- MQTT 消息 --> BE2

    BE1 -- SSE 长连接 --> USER
```

### 5.2 容器间通信拓扑

```mermaid
graph TD
    subgraph Docker_Network ["Docker 网络 (iotplatform_default)"]
        FE["frontend<br/>(端口 3000 映射到宿主机)"]
        BE["backend<br/>(端口 8000 映射到宿主机)"]
        PG["postgres<br/>(端口 5432 映射到宿主机)"]
        RD["redis<br/>(端口 6379 映射到宿主机)"]
        MQ["mosquitto<br/>(端口 1883, 9001 映射到宿主机)"]
    end

    %% 容器间通信（通过容器名 + 内部端口，不经过宿主机）
    FE -- HTTP :8000 --> BE
    BE -- postgresql+asyncpg :5432 --> PG
    BE -- redis:// :6379 --> RD
    BE -- MQTT :1883 --> MQ

    %% 外部访问（通过宿主机端口）
    USER[浏览器 / curl] -- HTTP 宿主机:3000 --> FE
    DEV[设备 / 模拟器] -- MQTT 宿主机:1883 --> MQ
    ADMIN[DBA 工具] -- 宿主机:5432 --> PG
    ADMIN -- 宿主机:6379 --> RD
```

---

## 六、状态图 (State Diagram)

### 6.1 命令状态流转

```mermaid
stateDiagram-v2
    [*] --> PENDING : 用户发送命令
    PENDING --> SENT : MQTT 发布成功
    SENT --> EXECUTED : 设备响应成功
    SENT --> FAILED : 设备响应失败 / 超时
    PENDING --> FAILED : MQTT 发布失败
    EXECUTED --> [*]
    FAILED --> [*]

    note right of PENDING
      后端创建命令记录
      status = PENDING
    end note

    note right of SENT
      命令已通过 MQTT 发送到设备
      status = SENT
    end note

    note right of EXECUTED
      设备返回执行结果
      output_data 已保存
      status = EXECUTED
    end note

    note right of FAILED
      记录 error_message
      status = FAILED
    end note
```

### 6.2 设备状态流转

```mermaid
stateDiagram-v2
    [*] --> OFFLINE : 设备创建
    OFFLINE --> ONLINE : 首次上报数据 / 状态上报
    ONLINE --> OFFLINE : 长时间未上报心跳
    ONLINE --> ERROR : 设备主动上报 error 状态
    ERROR --> ONLINE : 设备恢复正常
    OFFLINE --> [*] : 设备被删除
```

### 6.3 告警事件状态流转

```mermaid
stateDiagram-v2
    [*] --> TRIGGERED : 规则条件满足，生成告警
    TRIGGERED --> ACKNOWLEDGED : 用户点击"确认"
    ACKNOWLEDGED --> IN_PROGRESS : 用户标记为"处理中"
    IN_PROGRESS --> RESOLVED : 用户标记为"已解决"
    TRIGGERED --> RESOLVED : 直接标记为已解决
    RESOLVED --> ARCHIVED : 归档
    ARCHIVED --> [*]
```

---

## 七、活动图 (Activity Diagram)

### 7.1 告警规则检查流程

```mermaid
flowchart TD
    A[收到遥测数据<br/>Telemetry] --> B{验证设备密钥}
    B -->|失败| Z[记录警告日志，丢弃消息]
    B -->|成功| C[更新设备状态为 ONLINE<br/>更新 last_seen]
    C --> D[保存 Telemetry 到数据库]
    D --> E[获取所有匹配的启用中告警规则<br/>按 device_id / property_identifier 匹配]
    E --> F{是否有规则？}
    F -->|否| END[结束]
    F -->|是| G[进入循环检查每条规则]

    G --> H{检查冷却时间<br/>是否在 cooldown_seconds 内?}
    H -->|是| G
    H -->|否| I{检查静默时段<br/>当前时间在 silent_from_hour~silent_to_hour?}
    I -->|是| G
    I -->|否| J{阈值比较<br/>value operator threshold_value?}
    J -->|不满足| G
    J -->|满足| K[检查 duration_seconds<br/>是否满足持续时间]
    K -->|不满足| G
    K -->|满足| L[创建 AlertEvent 记录<br/>status=TRIGGERED]
    L --> M[通过 SSE 推送告警到前端]
    M --> N[更新 rule.last_triggered_at]
    N --> G

    G --> O{循环结束？}
    O -->|否| G
    O -->|是| END[结束]
```

### 7.2 用户从登录到查看告警完整流程

```mermaid
flowchart TD
    A[用户访问 http://host:3000] --> B{是否已登录?<br/>检查 localStorage token}
    B -->|是| E[跳转 /dashboard]
    B -->|否| C[显示登录页]

    C --> D[输入账号密码登录]
    D --> D1{登录成功?}
    D1 -->|否| C
    D1 -->|是| D2[保存 token]
    D2 --> E

    E --> F[前端加载仪表盘页面]
    F --> G[获取设备列表、统计数据]
    G --> H[建立 SSE 连接 /api/v1/sse/alerts]

    H --> I[用户可导航到任意页面]
    I --> I1[产品管理 - 创建/编辑产品]
    I --> I2[设备管理 - 创建设备/获取密钥]
    I --> I3[命令下发 - 发送命令到设备]
    I --> I4[遥测数据 - 查看设备上报]
    I --> I5[告警规则 - 创建规则]
    I --> I6[告警事件 - 实时查看告警]

    I6 --> J[SSE 连接保持]
    J -->|新告警到达| K[前端弹出通知 + 更新列表]
    J -->|连接断开| L[自动重连]

    I7[API密钥管理 - 创建密钥]
    I7 --> M[外部应用通过 X-API-Key 访问接口]
```

---

## 八、包图 (Package Diagram)

```mermaid
flowchart TB
    subgraph Frontend_Package ["frontend/ Vue.js 3 前端"]
        direction TB
        P1[views/ 页面组件<br/>Dashboard.vue, Devices.vue, Commands.vue, ...]
        P2[stores/ Pinia 状态管理<br/>auth.js, device.js, product.js]
        P3[services/ API 封装<br/>api.js]
        P4[router/ 路由<br/>index.js]
        P5[i18n/ 国际化<br/>locales/zh.js, en.js]
        P6[App.vue & main.js<br/>入口]
    end

    subgraph Backend_Package ["backend/ FastAPI 后端"]
        direction TB
        P10[main.py 应用入口]
        P11[api/ API 路由层<br/>devices.py, products.py, commands.py, telemetry.py, alerts.py, sse.py, apikeys.py, deps.py]
        P12[models/ ORM 模型<br/>models.py (11 个表模型 + 8 个枚举)]
        P13[schemas/ Pydantic Schema<br/>device.py, product.py, command.py]
        P14[security/ 认证模块<br/>auth.py (JWT / API Key)]
        P15[services/ 业务服务层<br/>alert_service.py, sse_service.py, init_service.py]
        P16[mqtt/ MQTT 客户端<br/>service.py, handler.py]
        P17[config.py 配置管理<br/>database.py 数据库连接]
    end

    subgraph Root_Package ["项目根目录"]
        direction TB
        P20[docker-compose.yml 容器编排]
        P21[Dockerfile.backend 后端镜像]
        P22[Dockerfile.frontend 前端镜像]
        P23[mosquitto/ MQTT 配置]
        P24[scripts/ 模拟器脚本<br/>product_device_simulator.py]
        P25[docs/ 文档目录<br/>USER_GUIDE.md, TECHNICAL_MANUAL.md, REQUIREMENTS.md, UML.md, ...]
    end

    P10 --> P11
    P11 --> P12
    P11 --> P13
    P11 --> P14
    P11 --> P15
    P11 --> P16
    P11 --> P17
    P15 --> P12
    P16 --> P15
    P14 --> P12
```

---

## 九、核心 API 时序图汇总

### 9.1 前后端交互总览

```mermaid
sequenceDiagram
    box "前端 (Browser, 端口 3000)"
        participant UI as Vue 页面
        participant API as axios
        participant EVENT as EventSource
    end
    box "后端 (FastAPI, 端口 8000)"
        participant HTTP as HTTP 接口
        participant AUTH as 认证
        participant BUS as 业务逻辑
        participant MSG as MQTT Handler
        participant SSE as SSE 推送
    end
    box "数据与消息"
        participant DB as PostgreSQL
        participant RD as Redis
        participant MQ as Mosquitto
    end

    UI ->> API: GET /dashboard 数据
    API ->> HTTP: 携带 Bearer Token
    HTTP ->> AUTH: 验证 Token
    AUTH ->> DB: 查询用户信息
    AUTH -->> HTTP: 验证通过
    HTTP ->> BUS: 查询设备总数 / 在线数 / 告警数
    BUS ->> DB: SQL 查询
    DB -->> BUS: 返回数据
    BUS -->> HTTP: 聚合数据
    HTTP -->> API: 200 OK
    API -->> UI: 更新页面展示

    UI ->> EVENT: new EventSource(/api/v1/sse/alerts)
    EVENT ->> SSE: 建立长连接
    SSE ->> AUTH: 验证 query 参数中的 token
    AUTH -->> SSE: 验证通过

    Note over MSG,UI: 当设备通过 MQTT 上报数据时
    MSG ->> BUS: 检查告警规则
    MSG ->> DB: 写入 Telemetry
    BUS ->> DB: 触发告警写入 AlertEvent
    BUS ->> SSE: broadcast_event
    SSE -->> EVENT: push: {message, severity, ...}
    EVENT -->> UI: onmessage 回调 → 弹出通知
```

---

## 十、总结

本 UML 文档覆盖了 IOTPlatform 的核心设计：

| 图类型 | 数量 | 内容 |
|--------|------|------|
| 类图 Class Diagram | 2 | 枚举类型 + 核心实体（11 个表 + 8 个枚举） |
| ER 图 ER Diagram | 1 | 完整数据库表关系图 |
| 用例图 Use Case Diagram | 1 | 33 个用例，覆盖用户/设备/第三方应用 |
| 时序图 Sequence Diagram | 4 | 登录、遥测+告警、命令下发、SSE 连接 |
| 组件图 Component Diagram | 2 | 前端/后端/数据层 三层架构 |
| 部署图 Deployment Diagram | 2 | Docker Compose 架构 + 通信拓扑 |
| 状态图 State Diagram | 3 | 命令/设备/告警状态机 |
| 活动图 Activity Diagram | 2 | 告警检查流程 + 用户完整流程 |
| 包图 Package Diagram | 1 | 项目目录结构 |
| **总计** | **16** | 覆盖系统设计的各个维度 |

### 渲染说明

本文档使用 **Mermaid** 语法，可在以下工具中直接渲染：
- VS Code（安装 Mermaid Preview / Markdown Preview Enhanced 插件）
- GitHub（原生支持 Mermaid）
- GitLab
- Typora / Obsidian
- 在线工具：https://mermaid.live
