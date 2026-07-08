# 智慧农业物联网平台 - 部署包

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
