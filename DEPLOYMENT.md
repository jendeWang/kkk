# IoT Platform Ubuntu 20.04 完整部署指南

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
    ca-certificates
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

### 5.2 克隆项目代码（假设代码已上传）

如果代码在本地：
```bash
# 将项目压缩包上传到服务器后解压
unzip iot-platform.zip -d /workspace/
```

或者从 Git 仓库克隆：
```bash
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

### 5.7 启动后端服务（开发模式）

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.8 后台运行（生产环境）

使用 systemd 服务：

```bash
cat > /etc/systemd/system/iot-backend.service << EOF
[Unit]
Description=IoT Platform Backend Service
After=network.target

[Service]
User=root
WorkingDirectory=/workspace/backend
ExecStart=/workspace/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

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

### 6.3 构建生产版本

```bash
npm run build
```

### 6.4 安装 Nginx（用于静态文件服务）

```bash
apt install -y nginx
```

### 6.5 配置 Nginx

```bash
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
}
EOF
```

启用站点：
```bash
ln -s /etc/nginx/sites-available/iot-frontend /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
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
  emqx/emqx:5.0
```

### 7.2 验证 EMQX

访问管理界面：http://<your-server-ip>:18083
- 默认用户名：admin
- 默认密码：public

---

## 八、配置防火墙（可选但推荐）

### 8.1 开启防火墙

```bash
ufw enable
```

### 8.2 允许必要端口

```bash
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS（如果使用SSL）
ufw allow 8000/tcp    # 后端API
ufw allow 1883/tcp    # MQTT
ufw allow 18083/tcp   # EMQX管理界面
```

### 8.3 查看状态

```bash
ufw status
```

---

## 九、访问平台

1. 打开浏览器访问：http://<your-server-ip>
2. 注册新账户或使用测试账户登录
3. 开始使用物联网平台

---

## 十、常见问题排查

### 10.1 端口冲突

检查端口占用：
```bash
netstat -tlnp | grep 8000
```

### 10.2 Python 虚拟环境问题

确保激活虚拟环境：
```bash
source /workspace/backend/venv/bin/activate
```

### 10.3 Nginx 日志

查看错误日志：
```bash
cat /var/log/nginx/error.log
```

### 10.4 后端日志

查看 systemd 日志：
```bash
journalctl -u iot-backend -f
```

### 10.5 权限问题

确保目录有写入权限：
```bash
chown -R www-data:www-data /workspace/frontend/dist
chmod -R 755 /workspace
```

---

## 十一、完整部署脚本（一键部署）

```bash
#!/bin/bash

echo "=== 开始部署 IoT Platform ==="

# 1. 更新系统
echo "Step 1: 更新系统"
apt update && apt upgrade -y

# 2. 安装基础依赖
echo "Step 2: 安装基础依赖"
apt install -y build-essential curl wget git vim unzip software-properties-common apt-transport-https ca-certificates

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
After=network.target

[Service]
User=root
WorkingDirectory=/workspace/backend
ExecStart=/workspace/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

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
}
EOF

ln -sf /etc/nginx/sites-available/iot-frontend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 8. 启动 MQTT Broker
echo "Step 8: 启动 MQTT Broker"
docker run -d --name emqx -p 1883:1883 -p 8083:8083 -p 8084:8084 -p 18083:18083 emqx/emqx:5.0

echo "=== 部署完成 ==="
echo "前端地址: http://localhost"
echo "后端API: http://localhost:8000"
echo "EMQX管理: http://localhost:18083"
```

使用方法：
```bash
chmod +x deploy.sh
./deploy.sh
```