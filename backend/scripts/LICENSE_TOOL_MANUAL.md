# License 授权生成工具使用手册

## 概述

本工具用于为智慧农业物联网平台生成学校授权文件。每个学校一份独立的授权，包含有效期、设备上限等信息，由发行方持有的私钥签名，学校无法伪造。

## 文件位置

```
backend/scripts/generate_license.py
```

## 首次使用

首次运行会自动生成 RSA-2048 密钥对：

```bash
cd backend
python scripts/generate_license.py --school "测试学校" --days 30 --devices 10
```

生成后：
- `backend/keys/.private` — **私钥（务必保管好，切勿泄露！）**
- `backend/keys/.public` — 公钥（随软件交付给学校）

**⚠️ 重要**：私钥丢失后无法生成新的授权文件，请备份到安全位置。

## 参数说明

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `--school` | 是 | 字符串 | 学校名称（如："某某职业技术学院"） |
| `--months` | 二选一 | 整数 | 授权时长（月），如 `6` 表示 6 个月 |
| `--days` | 二选一 | 整数 | 授权时长（天），如 `14` 表示 14 天 |
| `--date` | 二选一 | 字符串 | 过期日期（YYYY-MM-DD），如 `2027-01-15`，优先级高于 months/days |
| `--devices` | 否 | 整数 | 允许接入的最大设备数量，默认 `100` |
| `--out` | 否 | 字符串 | 自定义输出文件名，默认自动生成 |

## 使用示例

### 示例 1：授权 6 个月

```bash
python scripts/generate_license.py --school "某某职业技术学院" --months 6 --devices 100
```

输出：
- `licenses/某某职业技术学院_20270108.policy` — 授权文件
- `licenses/某某职业技术学院_deploy_public.key` — 公钥文件

### 示例 2：授权到指定日期

```bash
python scripts/generate_license.py --school "XX大学" --date 2027-06-30 --devices 50
```

输出：
- `licenses/XX大学_20270630.policy` — 授权文件
- `licenses/XX大学_deploy_public.key` — 公钥文件

### 示例 3：短期测试授权

```bash
python scripts/generate_license.py --school "测试学校" --days 7 --devices 10
```

输出：
- `licenses/测试学校_20260715.policy` — 授权文件
- `licenses/测试学校_deploy_public.key` — 公钥文件

### 示例 4：自定义输出文件名

```bash
python scripts/generate_license.py --school "ABC学院" --months 12 --devices 200 --out abc_annual.policy
```

输出：
- `licenses/abc_annual.policy` — 授权文件
- `licenses/ABC学院_deploy_public.key` — 公钥文件

## 交付给学校的文件

每次生成后，将以下两个文件交付给学校：

| 文件 | 部署后文件名 | 说明 |
|------|------------|------|
| `某某学校_YYYYMMDD.policy` | `.policy` | 授权文件（含学校名称、有效期、设备上限） |
| `某某学校_deploy_public.key` | `.auth` | 公钥文件（用于验证授权签名） |

## 部署步骤

学校收到文件后：

1. 将 `某某学校_YYYYMMDD.policy` 重命名为 `.policy`
2. 将 `某某学校_deploy_public.key` 重命名为 `.auth`
3. 放到服务器 `backend/` 目录下
4. 重启后端服务

```bash
# 学校服务器上执行
cp 某某学校_20270630.policy /opt/iot-platform/backend/.policy
cp 某某学校_deploy_public.key /opt/iot-platform/backend/.auth
systemctl restart iot-platform
```

## 授权状态说明

| 状态 | 表现 | 处理建议 |
|------|------|---------|
| 授权有效 | 所有功能正常使用 | 无需处理 |
| 授权过期（只读） | 可查看数据，不可新增/控制 | 联系发行方续期 |
| 授权失效 | 系统拒绝启动 | 检查授权文件是否正确 |

## 硬件绑定规则

| 场景 | 行为 |
|------|------|
| 首次部署 | 自动绑定当前服务器硬件 |
| 签发 30 天内迁移到新服务器 | 允许，自动更新绑定 |
| 签发超过 30 天迁移 | 拒绝启动，需重新申请授权 |

## 常见问题

**Q: 学校服务器重装系统后授权还有效吗？**
A: 只要 `.policy` 和 `.auth` 文件还在，复制回 `backend/` 目录即可。若已超过签发 30 天，请重新申请。

**Q: 可以修改授权文件里的设备数量或过期时间吗？**
A: 不可以。任何修改都会导致 RSA 签名验证失败，系统拒绝启动。

**Q: 需要联网才能生成授权吗？**
A: 不需要。密钥对在本地生成，授权文件在本地签名。

**Q: 私钥丢失了怎么办？**
A: 无法恢复，请立即联系技术支持。建议提前备份私钥。

## 许可证续期流程

1. 学校联系发行方申请续期
2. 发行方重新生成授权文件（指定新的有效期）
3. 学校替换服务器上的 `.policy` 文件
4. 重启后端服务即可

示例：为学校续期 1 年

```bash
python scripts/generate_license.py --school "某某职业技术学院" --months 12 --devices 100
```

## 安全注意事项

1. **私钥安全**：`keys/.private` 切勿上传到任何公共仓库或分享给他人
2. **授权文件管理**：记录每个学校的授权信息（学校名称、有效期、设备数量）
3. **备份**：定期备份私钥和授权记录

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07 | 初始版本，支持 RSA-2048 签名、有效期控制、设备上限、硬件绑定 |
