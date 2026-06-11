# IoT Platform 部署文档

## 一、项目概述

本项目是一个物联网平台，包含前端和后端两部分：
- **前端**：Vue 3 + Element Plus
- **后端**：FastAPI + SQLite
- **MQTT Broker**：需要独立部署（如 EMQX）

## 二、环境要求

### 2.1 基础环境
- Python 3.10+
- Node.js 18+
- npm 或 yarn

### 2.2 可选依赖
- MQTT Broker（推荐 EMQX 5.x）

## 三、后端部署

### 3.1 安装依赖

```bash
cd /workspace/backend
pip install -r requirements.txt
```

### 3.2 启动后端服务

```bash
cd /workspace/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**服务访问**：http://localhost:8000

**API文档**：http://localhost:8000/docs

### 3.3 配置说明

后端使用 SQLite 数据库，数据文件位于：
- `/workspace/backend/app.db`

## 四、前端部署

### 4.1 安装依赖

```bash
cd /workspace/frontend
npm install
```

### 4.2 开发模式运行

```bash
cd /workspace/frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

### 4.3 生产构建

```bash
cd /workspace/frontend
npm run build
```

构建产物位于 `dist` 目录，可部署到 Nginx 或静态文件服务器。

### 4.4 配置说明

前端配置文件：`/workspace/frontend/src/services/api.js`

```javascript
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
})
```

## 五、MQTT Broker 部署（可选）

### 5.1 使用 EMQX（Docker方式）

```bash
docker run -d --name emqx -p 1883:1883 -p 8083:8083 -p 8084:8084 -p 18083:18083 emqx/emqx:5.0
```

### 5.2 配置 MQTT 连接

后端 MQTT 配置位于：`/workspace/backend/app/core/config.py`

```python
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
```

## 六、完整启动流程

```bash
# 1. 启动 MQTT Broker（可选）
docker run -d --name emqx -p 1883:1883 emqx/emqx:5.0

# 2. 启动后端服务
cd /workspace/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 启动前端服务（新开终端）
cd /workspace/frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

## 七、访问平台

1. 打开浏览器访问：http://localhost:3000
2. 注册新账户或使用测试账户登录
3. 开始使用物联网平台

## 八、常见问题

### 8.1 端口冲突

如果端口被占用，可以修改端口：

```bash
# 后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# 前端
npm run dev -- --host 0.0.0.0 --port 3001
```

### 8.2 跨域问题

后端已配置 CORS，允许前端访问。如果遇到跨域错误，请检查：
- 后端服务是否正常运行
- 前端 API 配置是否正确

### 8.3 数据库连接问题

确保 SQLite 数据库目录有写入权限：

```bash
chmod 755 /workspace/backend
```

---

## 3. Windows PyCharm vs Ubuntu 20.04 运行对比

| 维度 | Windows PyCharm | Ubuntu 20.04 |
|------|----------------|--------------|
| **开发体验** | 图形界面友好，调试方便 | 命令行为主，轻量高效 |
| **性能** | 资源占用较高 | 资源占用较低 |
| **部署测试** | 需模拟 Linux 环境 | 与生产环境一致 |
| **MQTT Broker** | 需要额外安装 | 原生支持 Docker |
| **推荐场景** | 日常开发、调试 | 部署、性能测试 |

**建议**：
- **开发阶段**：使用 Windows + PyCharm，调试方便，界面友好
- **部署/测试**：使用 Ubuntu 20.04，环境更接近生产环境，支持 Docker

如果需要同时兼顾开发和部署，可以使用 WSL2（Windows Subsystem for Linux）在 Windows 上运行 Ubuntu 环境。