#!/bin/bash
# 智慧农业物联网平台一键安装脚本
# 适用于 Ubuntu 20.04+

set -e

INSTALL_DIR="/opt/iot-platform"
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo " 智慧农业物联网平台 安装脚本"
echo "=========================================="

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用 root 权限运行此脚本"
    exit 1
fi

# 安装依赖
echo "[1/5] 安装系统依赖..."
apt-get update
apt-get install -y python3 python3-pip nginx

# 创建安装目录
echo "[2/5] 创建安装目录..."
mkdir -p $INSTALL_DIR

# 复制文件
echo "[3/5] 复制程序文件..."
cp -r $CURRENT_DIR/backend $INSTALL_DIR/
cp -r $CURRENT_DIR/frontend $INSTALL_DIR/

# 安装 Python 依赖
echo "[4/5] 安装 Python 依赖..."
cd $INSTALL_DIR/backend
pip3 install -r requirements.txt --break-system-packages || pip3 install -r requirements.txt

# 配置 Nginx
echo "[5/5] 配置 Nginx..."
cp $INSTALL_DIR/frontend/nginx.conf /etc/nginx/sites-available/iot-platform
ln -sf /etc/nginx/sites-available/iot-platform /etc/nginx/sites-enabled/iot-platform
nginx -t && systemctl reload nginx

# 创建 systemd 服务
cat > /etc/systemd/system/iot-platform.service << 'EOF'
[Unit]
Description=IoT Platform Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iot-platform/backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable iot-platform

echo ""
echo "=========================================="
echo " 安装完成!"
echo "=========================================="
echo ""
echo "后续步骤:"
echo "  1. 将授权文件放到 $INSTALL_DIR/backend/.policy"
echo "  2. 将公钥文件放到 $INSTALL_DIR/backend/.auth"
echo "  3. 启动服务: systemctl start iot-platform"
echo "  4. 访问平台: http://your-server-ip"
echo ""
echo "默认管理员账号: admin / admin123"
echo "请登录后立即修改密码!"
echo ""
