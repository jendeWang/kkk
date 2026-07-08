#!/usr/bin/env python3
"""
构建部署包脚本
只将授权核心模块编译为 .so，其他源码保持 .py 格式可交付
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 路径配置
BACKEND_DIR = Path("/workspace/backend")
DEPLOY_DIR = Path("/workspace/deploy")
BACKEND_DEPLOY = DEPLOY_DIR / "backend"
FRONTEND_DEPLOY = DEPLOY_DIR / "frontend"
SCRIPTS_DEPLOY = DEPLOY_DIR / "scripts"

# 需要编译的核心模块（授权相关）
LICENSE_MODULE = "app/core/license.py"

def run(cmd, cwd=None):
    """执行命令"""
    print(f"[RUN] {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        sys.exit(1)
    return result.stdout

def clean_deploy():
    """清空部署目录"""
    for d in [BACKEND_DEPLOY, FRONTEND_DEPLOY, SCRIPTS_DEPLOY]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

def compile_license():
    """将 license.py 编译为 .so"""
    print("\n[STEP] 编译授权模块为 .so 文件...")

    # 创建临时编译目录
    build_dir = BACKEND_DIR / "_build_temp"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    # 复制 license.py 到编译目录
    license_src = BACKEND_DIR / LICENSE_MODULE
    license_copy = build_dir / "license.py"
    shutil.copy(license_src, license_copy)

    # 创建 setup.py
    setup_content = '''
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("license.py", language_level=3),
)
'''
    setup_file = build_dir / "setup.py"
    setup_file.write_text(setup_content)

    # 编译
    run("python setup.py build_ext --inplace", cwd=build_dir)

    # 找到生成的 .so 文件
    so_files = list(build_dir.glob("license*.so"))
    if not so_files:
        print("[ERROR] 未找到编译后的 .so 文件")
        sys.exit(1)

    so_file = so_files[0]
    print(f"[OK] 编译成功: {so_file.name}")

    # 复制到部署目录（保持原目录结构）
    target_dir = BACKEND_DEPLOY / "app" / "core"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_so = target_dir / "license.so"
    shutil.copy(so_file, target_so)
    print(f"[OK] 已复制到: {target_so}")

    # 清理临时目录
    shutil.rmtree(build_dir)

def copy_backend_source():
    """复制后端源码（排除 license.py，用 .so 替代）"""
    print("\n[STEP] 复制后端源码...")

    # 复制除 license.py 外的所有源码
    for item in BACKEND_DIR.iterdir():
        if item.name in ["_build_temp", "__pycache__", "*.pyc", "logs", ".state", "keys"]:
            continue
        if item.is_file() and item.suffix == ".py":
            if item.name == "requirements.txt":
                shutil.copy(item, BACKEND_DEPLOY / item.name)
            elif item.name not in ["test_rollback.py"]:
                shutil.copy(item, BACKEND_DEPLOY / item.name)
        elif item.is_dir() and item.name == "app":
            # 复制 app 目录，但排除 license.py 和 __pycache__
            copy_app_dir(item, BACKEND_DEPLOY / "app")
        elif item.is_dir() and item.name in ["scripts"]:
            # 复制脚本目录
            target_scripts = BACKEND_DEPLOY / "scripts"
            target_scripts.mkdir(exist_ok=True)
            for f in item.iterdir():
                if f.name in ["generate_license.py", "build_license.py"]:
                    # 授权相关脚本不随学校交付
                    continue
                if f.is_file():
                    shutil.copy(f, target_scripts / f.name)

    # 创建空的数据库
    db_file = BACKEND_DEPLOY / "iot_platform.db"
    if not db_file.exists():
        db_file.touch()

    # 复制授权模板文件（空文件，由您填充）
    (BACKEND_DEPLOY / ".auth").touch()
    (BACKEND_DEPLOY / ".policy").touch()

    print("[OK] 后端源码复制完成")

def copy_app_dir(src, dst):
    """复制 app 目录"""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in ["__pycache__"]:
            continue
        if item.is_dir():
            copy_app_dir(item, dst / item.name)
        elif item.is_file() and item.suffix == ".py":
            # 排除 license.py（用 .so 替代）
            if item.name == "license.py" and item.parent.name == "core":
                continue
            shutil.copy(item, dst / item.name)
        elif item.is_file():
            shutil.copy(item, dst / item.name)

def copy_frontend():
    """复制前端构建产物"""
    print("\n[STEP] 复制前端...")

    frontend_src = Path("/workspace/frontend")
    if not frontend_src.exists():
        print("[WARN] 前端目录不存在，跳过")
        return

    # 复制 dist 目录（如果存在）
    dist_src = frontend_src / "dist"
    if dist_src.exists():
        # 使用 shutil.copytree 并手动处理已存在目录
        dst_dist = FRONTEND_DEPLOY / "dist"
        if dst_dist.exists():
            shutil.rmtree(dst_dist)
        shutil.copytree(dist_src, dst_dist)
        print("[OK] 前端 dist 复制完成")
    else:
        print("[WARN] 前端未构建，请先运行 npm run build")

def create_configs():
    """创建配置文件"""
    print("\n[STEP] 创建配置文件...")

    # requirements.txt
    req_file = BACKEND_DEPLOY / "requirements.txt"
    req_content = """
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
aiosqlite==0.19.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
gunicorn==21.2.0
redis==5.0.1
cryptography>=3.4.0
"""
    req_file.write_text(req_content.strip())

    # 启动脚本
    start_sh = BACKEND_DEPLOY / "start.sh"
    start_content = """#!/bin/bash
# 智慧农业物联网平台启动脚本

cd "$(dirname "$0")"

# 检查授权文件
if [ ! -f ".policy" ]; then
    echo "错误: 未找到授权文件 (.policy)"
    echo "请联系发行方获取授权"
    exit 1
fi

if [ ! -f ".auth" ]; then
    echo "错误: 未找到公钥文件 (.auth)"
    exit 1
fi

# 启动后端
echo "正在启动智慧农业物联网平台..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
    start_sh.write_text(start_content)
    start_sh.chmod(0o755)

    # Nginx 配置模板
    nginx_conf = FRONTEND_DEPLOY / "nginx.conf"
    nginx_content = """# 智慧农业物联网平台 Nginx 配置
# 请根据实际域名和路径调整

server {
    listen 80;
    server_name your-domain.com;  # 请修改为实际域名

    # 前端静态文件
    location / {
        root /opt/iot-platform/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket/SSE 支持
    location /api/v1/sse/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
    }
}
"""
    nginx_conf.write_text(nginx_content)

    print("[OK] 配置文件创建完成")

def create_install_script():
    """创建一键安装脚本"""
    print("\n[STEP] 创建安装脚本...")

    install_sh = DEPLOY_DIR / "install.sh"
    content = """#!/bin/bash
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
"""
    install_sh.write_text(content)
    install_sh.chmod(0o755)

    print("[OK] 安装脚本创建完成")

def create_readme():
    """创建部署说明"""
    print("\n[STEP] 创建部署说明...")

    readme = DEPLOY_DIR / "README.md"
    content = """# 智慧农业物联网平台 - 部署包

## 目录结构

```
deploy/
├── backend/              # 后端程序
│   ├── app/              # 应用代码
│   │   └── core/
│   │       └── license.so    # 授权模块（已编译）
│   ├── .auth             # 公钥文件（需填充）
│   ├── .policy           # 授权文件（需填充）
│   ├── requirements.txt  # Python 依赖
│   └── start.sh          # 启动脚本
├── frontend/             # 前端程序
│   ├── dist/             # 构建产物
│   └── nginx.conf        # Nginx 配置模板
├── install.sh            # 一键安装脚本
└── README.md             # 本文件
```

## 快速部署

### 方式一：一键安装（推荐）

1. 将整个 `deploy/` 目录上传到服务器
2. 运行安装脚本：
   ```bash
   sudo ./install.sh
   ```
3. 将授权文件放到 `/opt/iot-platform/backend/` 目录：
   - `.policy` — 授权文件
   - `.auth` — 公钥文件
4. 启动服务：
   ```bash
   systemctl start iot-platform
   ```

### 方式二：手动安装

1. 安装依赖：
   ```bash
   apt-get update
   apt-get install -y python3 python3-pip nginx
   ```

2. 复制程序到目标目录：
   ```bash
   mkdir -p /opt/iot-platform
   cp -r deploy/backend /opt/iot-platform/
   cp -r deploy/frontend /opt/iot-platform/
   ```

3. 安装 Python 依赖：
   ```bash
   cd /opt/iot-platform/backend
   pip3 install -r requirements.txt
   ```

4. 配置授权文件：
   ```bash
   # 将发行方提供的授权文件复制到 backend 目录
   cp your-school.policy /opt/iot-platform/backend/.policy
   cp your-school.key /opt/iot-platform/backend/.auth
   ```

5. 启动后端：
   ```bash
   cd /opt/iot-platform/backend
   ./start.sh
   ```

6. 配置 Nginx：
   ```bash
   cp /opt/iot-platform/frontend/nginx.conf /etc/nginx/sites-available/iot-platform
   ln -s /etc/nginx/sites-available/iot-platform /etc/nginx/sites-enabled/
   nginx -t && systemctl reload nginx
   ```

## 授权说明

本平台采用离线授权机制：

- **授权文件 `.policy`**：包含学校名称、过期时间、设备上限等信息，由发行方生成
- **公钥文件 `.auth`**：用于验证授权文件的签名
- **硬件绑定**：授权会绑定到服务器硬件特征，签发 30 天内允许迁移，超过 30 天需重新申请

### 授权状态

| 状态 | 说明 |
|------|------|
| 授权有效 | 所有功能正常使用 |
| 授权过期（只读） | 可查看数据，不可新增设备或下发命令 |
| 授权失效 | 系统拒绝启动 |

## 默认账号

- 管理员：`admin` / `admin123`
- 请登录后立即修改密码

## 常见问题

**Q: 启动时报"授权校验失败"?**
A: 检查 `.policy` 和 `.auth` 文件是否存在且内容正确。

**Q: 迁移到新服务器后授权失效?**
A: 授权签发 30 天内允许迁移，超过 30 天请联系发行方重新申请。

**Q: 授权过期后数据会丢失吗?**
A: 不会。过期后进入只读模式，数据可查看但不可修改，续期后恢复正常。

## 技术支持

如有问题，请联系发行方。
"""
    readme.write_text(content)

    print("[OK] 部署说明创建完成")

def main():
    print("=" * 50)
    print(" 智慧农业物联网平台 - 部署包构建")
    print("=" * 50)

    clean_deploy()
    compile_license()
    copy_backend_source()
    copy_frontend()
    create_configs()
    create_install_script()
    create_readme()

    print("\n" + "=" * 50)
    print(" 构建完成!")
    print("=" * 50)
    print(f"\n部署包位置: {DEPLOY_DIR}")
    print("\n后续步骤:")
    print("  1. 构建前端: cd /workspace/frontend && npm run build")
    print("  2. 重新运行此脚本以包含前端")
    print("  3. 将 deploy/ 目录打包交付给学校")

if __name__ == "__main__":
    main()