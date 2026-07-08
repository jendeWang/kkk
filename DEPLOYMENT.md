# IoT Platform Ubuntu 20.04 完整部署指南

> **版本**: v1.0
> **更新日期**: 2026-06-11
> **状态**: 生产就绪

---

## 一、系统初始化（刚安装完Ubuntu 20.04）

### 1.1 切换到root用户

```bash
sudo -i
```

### 1.2 更新apt源（可选但推荐）

备份原有源：
```bash
cp /etc/apt/sources.list /etc/apt/sources.list.bak
```

修改为国内源（阿里云）：
```bash
cat > /etc/apt/sources.list << EOF
deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
EOF
```

### 1.3 更新系统包

```bash
apt update && apt upgrade -y
```

### 1.4 安装基础依赖

```bash
apt install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    net-tools \
    ufw
```

---

## 二、安装 Python 3.10+

### 2.1 添加 deadsnakes PPA（Ubuntu 20.04 默认 Python 3.8）

```bash
add-apt-repository -y ppa:deadsnakes/ppa
apt update
```

### 2.2 安装 Python 3.10

```bash
apt install -y python3.10 python3.10-dev python3.10-venv python3-pip
```

### 2.3 设置 Python 3.10 为默认

```bash
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
update-alternatives --config python3
```

### 2.4 升级 pip

```bash
python3 -m pip install --upgrade pip
```

---

## 三、安装 Node.js 18+

### 3.1 添加 NodeSource 仓库

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
```

### 3.2 安装 Node.js

```bash
apt install -y nodejs
```

### 3.3 验证安装

```bash
node --version   # 应显示 v18.x.x
npm --version    # 应显示 9.x.x
```

### 3.4 配置 npm 国内镜像（可选）

```bash
npm config set registry https://registry.npmmirror.com
```

---

## 四、安装 Docker（用于 MQTT Broker）

### 4.1 安装 Docker 依赖

```bash
apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### 4.2 添加 Docker GPG 密钥

```bash
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

### 4.3 添加 Docker 仓库

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 4.4 安装 Docker 引擎

```bash
apt update && apt install -y docker-ce docker-ce-cli containerd.io
```

### 4.5 启动 Docker 服务

```bash
systemctl enable docker
systemctl start docker
```

### 4.6 验证 Docker

```bash
docker --version
docker run hello-world
```

---

## 五、部署后端服务

### 5.1 创建工作目录

```bash
mkdir -p /workspace
cd /workspace
```

### 5.2 克隆项目代码

```bash
# 将项目压缩包上传到服务器后解压
unzip iot-platform.zip -d /workspace/

# 或者从 Git 仓库克隆
git clone <your-repo-url> /workspace
```

### 5.3 进入后端目录

```bash
cd /workspace/backend
```

### 5.4 创建虚拟环境

```bash
python3 -m venv venv
```

### 5.5 激活虚拟环境

```bash
source venv/bin/activate
```

### 5.6 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 5.7 后端配置说明

后端服务使用 SQLite 数据库，无需额外配置数据库服务。

**配置文件位置**: `backend/.env`
```env
# 服务端口
PORT=8000

# JWT密钥（生产环境请修改）
SECRET_KEY=your-secret-key-here

# 数据库路径
DATABASE_URL=sqlite:///./sql_app.db

# MQTT配置
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USER=admin
MQTT_PASSWORD=public
```

### 5.8 启动后端服务（开发模式）

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.9 后台运行（生产环境）

使用 systemd 服务：

```bash
cat > /etc/systemd/system/iot-backend.service << EOF
[Unit]
Description=IoT Platform Backend Service
After=network.target docker.service

[Service]
User=root
WorkingDirectory=/workspace/backend
ExecStart=/workspace/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment="PYTHONPATH=/workspace/backend"

[Install]
WantedBy=multi-user.target
EOF
```

启动服务：
```bash
systemctl daemon-reload
systemctl enable iot-backend
systemctl start iot-backend
```

查看状态：
```bash
systemctl status iot-backend
```

---

## 六、部署前端服务

### 6.1 进入前端目录

```bash
cd /workspace/frontend
```

### 6.2 安装依赖

```bash
npm install
```

### 6.3 前端配置说明

**配置文件位置**: `frontend/src/config.js`
```javascript
export default {
  apiBaseUrl: '/api',
  timeout: 30000
}
```

### 6.4 构建生产版本

```bash
npm run build
```

### 6.5 安装 Nginx（用于静态文件服务）

```bash
apt install -y nginx
```

### 6.6 配置 Nginx

```bash
cat > /etc/nginx/sites-available/iot-frontend << EOF
server {
    listen 80;
    server_name localhost;

    # 前端静态文件
    location / {
        root /workspace/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # SSE支持
    location /api/v1/sse/ {
        proxy_pass http://localhost:8000/api/v1/sse/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
}
EOF
```

启用站点：
```bash
ln -sf /etc/nginx/sites-available/iot-frontend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
```

测试配置：
```bash
nginx -t
```

重启 Nginx：
```bash
systemctl restart nginx
```

---

## 七、部署 MQTT Broker（EMQX）

### 7.1 使用 Docker 启动 EMQX

```bash
docker run -d \
  --name emqx \
  -p 1883:1883 \
  -p 8083:8083 \
  -p 8084:8084 \
  -p 18083:18083 \
  --restart unless-stopped \
  emqx/emqx:5.0
```

### 7.2 验证 EMQX

访问管理界面：http://<your-server-ip>:18083
- 默认用户名：admin
- 默认密码：public

### 7.3 配置 EMQX（可选）

登录管理界面后，可以：
1. 创建新用户
2. 配置认证方式
3. 设置 ACL 规则

---

## 八、启动设备模拟器（可选）

设备模拟器用于模拟物联网设备发送遥测数据和接收命令。

### 8.1 进入模拟器目录

```bash
cd /workspace/simulator
```

### 8.2 安装依赖

```bash
pip install -r requirements.txt
```

### 8.3 启动模拟器

```bash
python simulator.py
```

### 8.4 后台运行模拟器

```bash
cat > /etc/systemd/system/iot-simulator.service << EOF
[Unit]
Description=IoT Device Simulator
After=network.target iot-backend.service

[Service]
User=root
WorkingDirectory=/workspace/simulator
ExecStart=/workspace/backend/venv/bin/python simulator.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

启动服务：
```bash
systemctl daemon-reload
systemctl enable iot-simulator
systemctl start iot-simulator
```

---

## 九、配置防火墙（推荐）

### 9.1 开启防火墙

```bash
ufw enable
```

### 9.2 允许必要端口

```bash
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS（如果使用SSL）
ufw allow 8000/tcp    # 后端API
ufw allow 1883/tcp    # MQTT
ufw allow 18083/tcp   # EMQX管理界面
```

### 9.3 查看状态

```bash
ufw status
```

---

## 十、访问平台

### 10.1 访问地址

- **前端界面**: http://<your-server-ip>
- **后端API**: http://<your-server-ip>:8000
- **API文档**: http://<your-server-ip>:8000/docs
- **EMQX管理**: http://<your-server-ip>:18083

### 10.2 测试账户

系统预置测试账户：
- **用户名**: admin
- **密码**: admin123

> ⚠️ **安全提醒**: 生产环境请修改默认密码！

### 10.3 注册新账户

访问首页后，点击"注册新账户"链接创建新账户。

---

## 十一、功能模块说明

### 11.1 仪表盘
- 产品总数统计
- 设备总数统计
- 在线设备统计
- 告警总数统计
- 设备状态分布图表
- 最近告警列表

### 11.2 产品管理
- 产品CRUD操作
- 属性管理（名称、类型、读写权限）
- 服务管理（含参数定义）
- 事件管理

### 11.3 设备管理
- 设备CRUD操作
- 设备密钥管理
- 设备状态监控

### 11.4 遥测数据
- 设备数据查看
- 属性筛选
- 时间范围查询

### 11.5 命令下发
- 设备选择
- 服务选择
- 参数表单/JSON模式
- 命令状态跟踪

### 11.6 告警规则
- 阈值告警配置
- 设备状态告警
- 规则启用/禁用

### 11.7 告警事件
- 告警列表
- 确认/解决操作

### 11.8 API密钥管理
- 密钥创建/删除
- 权限级别设置

---

## 十二、常见问题排查

### 12.1 端口冲突

检查端口占用：
```bash
netstat -tlnp | grep 8000
```

### 12.2 Python 虚拟环境问题

确保激活虚拟环境：
```bash
source /workspace/backend/venv/bin/activate
```

### 12.3 Nginx 日志

查看错误日志：
```bash
cat /var/log/nginx/error.log
```

### 12.4 后端日志

查看 systemd 日志：
```bash
journalctl -u iot-backend -f
```

### 12.5 权限问题

确保目录有写入权限：
```bash
chown -R www-data:www-data /workspace/frontend/dist
chmod -R 755 /workspace
```

### 12.6 MQTT 连接问题

检查 EMQX 状态：
```bash
docker logs emqx
```

### 12.7 前端构建失败

清理缓存后重新构建：
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 十三、完整部署脚本（一键部署）

```bash
#!/bin/bash

set -e

echo "=== 开始部署 IoT Platform ==="

# 1. 更新系统
echo "Step 1: 更新系统"
apt update && apt upgrade -y

# 2. 安装基础依赖
echo "Step 2: 安装基础依赖"
apt install -y build-essential curl wget git vim unzip software-properties-common apt-transport-https ca-certificates net-tools ufw

# 3. 安装 Python 3.10
echo "Step 3: 安装 Python 3.10"
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.10 python3.10-dev python3.10-venv python3-pip
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
python3 -m pip install --upgrade pip

# 4. 安装 Node.js 18
echo "Step 4: 安装 Node.js 18"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
npm config set registry https://registry.npmmirror.com

# 5. 安装 Docker
echo "Step 5: 安装 Docker"
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update && apt install -y docker-ce docker-ce-cli containerd.io
systemctl enable docker
systemctl start docker

# 6. 部署后端
echo "Step 6: 部署后端服务"
cd /workspace/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 创建 systemd 服务
cat > /etc/systemd/system/iot-backend.service << EOF
[Unit]
Description=IoT Platform Backend Service
After=network.target docker.service

[Service]
User=root
WorkingDirectory=/workspace/backend
ExecStart=/workspace/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment="PYTHONPATH=/workspace/backend"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable iot-backend
systemctl start iot-backend

# 7. 部署前端
echo "Step 7: 部署前端服务"
cd /workspace/frontend
npm install
npm run build

# 安装 Nginx
apt install -y nginx

# 配置 Nginx
cat > /etc/nginx/sites-available/iot-frontend << EOF
server {
    listen 80;
    server_name localhost;

    location / {
        root /workspace/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /api/v1/sse/ {
        proxy_pass http://localhost:8000/api/v1/sse/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/iot-frontend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 8. 启动 MQTT Broker
echo "Step 8: 启动 MQTT Broker"
docker run -d --name emqx --restart unless-stopped -p 1883:1883 -p 8083:8083 -p 8084:8084 -p 18083:18083 emqx/emqx:5.0

# 9. 配置防火墙
echo "Step 9: 配置防火墙"
ufw enable
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 1883/tcp
ufw allow 18083/tcp

echo "=== 部署完成 ==="
echo "前端地址: http://localhost"
echo "后端API: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "EMQX管理: http://localhost:18083"
echo "测试账户: admin / admin123"
```

使用方法：
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 十四、版本更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-06-11 | v1.0 | 初始版本发布，包含完整CRUD功能 |
| | | 支持服务参数定义（默认值、可选值、范围限制、正则） |
| | | 命令下发双模式（表单模式+JSON高级模式） |
| | | 国际化支持（中文/英文） |
| | | 设备模拟器支持 |

---

## 十五、技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue.js | 3.4.x |
| UI组件库 | Element Plus | 2.5.x |
| 状态管理 | Pinia | 2.1.x |
| 路由 | Vue Router | 4.2.x |
| 国际化 | vue-i18n | 9.9.x |
| 图表 | ECharts | 5.4.x |
| 后端框架 | FastAPI | 0.109.x |
| 数据库 | PostgreSQL | 16.x |
| 缓存 | Redis | 7.x |
| ORM | SQLAlchemy | 2.0.x |
| MQTT Broker | EMQX | 5.0 |
| WSGI服务器 | Gunicorn | 21.2.x |
| 构建工具 | Vite | 5.0.x |

---

## 十六、Docker Compose 一键部署（推荐）

### 16.1 前提条件

- 安装 Docker 20.10+
- 安装 Docker Compose 2.0+

```bash
# 检查安装
docker --version
docker compose version
```

### 16.2 部署步骤

```bash
# 1. 进入项目目录
cd /workspace

# 2. 启动所有服务
docker compose up -d

# 3. 查看服务状态
docker compose ps

# 4. 查看日志
docker compose logs -f
```

### 16.3 服务访问

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端** | http://localhost | Web界面 |
| **后端API** | http://localhost:8000 | API文档: http://localhost:8000/docs |
| **EMQX管理** | http://localhost:18083 | 用户名: admin / 密码: public |
| **PostgreSQL** | localhost:5432 | 用户: iot_user / 密码: iot_password |
| **Redis** | localhost:6379 | 无认证 |

### 16.4 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 停止并删除数据卷（慎用）
docker compose down -v

# 重启某个服务
docker compose restart backend

# 查看服务日志
docker compose logs -f backend

# 重新构建镜像
docker compose build --no-cache

# 进入后端容器
docker exec -it iot_backend sh

# 进入数据库
docker exec -it iot_postgres psql -U iot_user -d iot_platform
```

### 16.5 健康检查

```bash
# 检查所有服务健康状态
curl http://localhost/health
docker compose ps

# 检查后端API
curl http://localhost:8000/api/v1/health

# 检查 EMQX
curl http://localhost:18083/api/v5/health
```

---

## 十七、性能优化说明

### 17.1 Gunicorn 多进程配置

后端使用 Gunicorn 运行，默认 worker 数量为 CPU 核心数 × 2 + 1。

```bash
# 自定义 worker 数量
docker compose run -e WORKERS=8 -d backend
```

### 17.2 PostgreSQL 连接池

PostgreSQL 配置了连接池参数，适合 100-500 设备规模。

### 17.3 Redis 缓存

系统使用 Redis 进行会话和热点数据缓存，提高响应速度。

---

## 十八、故障排查

### 18.1 服务无法启动

```bash
# 查看详细日志
docker compose logs backend

# 检查端口占用
netstat -tlnp | grep -E '5432|6379|1883|8000|80'
```

### 18.2 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker compose logs postgres

# 进入 PostgreSQL 容器测试连接
docker exec -it iot_postgres psql -U iot_user -d iot_platform -c "SELECT 1;"
```

### 18.3 MQTT 连接失败

```bash
# 检查 EMQX 状态
docker compose logs emqx

# 访问 EMQX Dashboard
# http://localhost:18083
```

### 18.4 清理重建

```bash
# 完全清理（删除所有数据）
docker compose down -v

# 重新构建并启动
docker compose down -v --rmi all
docker compose build --no-cache
docker compose up -d
```

---

## 十九、安全建议

### 19.1 生产环境必做

1. **修改默认密码**
   ```bash
   # EMQX
   EMQX_Dashboard__DEFAULT_PASSWORD=your-secure-password

   # PostgreSQL
   POSTGRES_PASSWORD=your-secure-password

   # JWT Secret
   SECRET_KEY=your-256-bit-secret-key
   ```

2. **启用 SSL/TLS**
   ```yaml
   # 在 nginx 配置中添加证书
   ssl_certificate /path/to/cert.pem;
   ssl_certificate_key /path/to/key.pem;
   ```

3. **配置防火墙**
   ```bash
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw deny 5432/tcp  # 仅允许容器内访问
   ufw deny 6379/tcp  # 仅允许容器内访问
   ```

4. **限制 PostgreSQL 访问**
   ```bash
   # 仅允许本地和容器网络访问
   # PostgreSQL 默认配置已限制为 localhost
   ```

---

## 二十、版本更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-06-11 | v1.0 | 初始版本发布，包含完整CRUD功能 |
| | | 支持服务参数定义（默认值、可选值、范围限制、正则） |
| | | 命令下发双模式（表单模式+JSON高级模式） |
| | | 国际化支持（中文/英文） |
| | | 设备模拟器支持 |
| 2026-06-11 | v1.1 | **Docker Compose 部署支持** |
| | | PostgreSQL 数据库替代 SQLite |
| | | Redis 缓存支持 |
| | | EMQX MQTT Broker |
| | | Gunicorn 多进程部署 |
| | | Nginx WebSocket/SSE 支持 |
| | | 支持 100-500 设备规模 |
