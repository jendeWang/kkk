#!/usr/bin/env python3
"""
授权策略生成工具
仅供发行方使用，用于为每个学校生成带签名的授权文件

用法示例:
    python scripts/generate_license.py --school "某某职业技术学院" --months 6 --devices 100
    python scripts/generate_license.py --school "XX大学" --date "2027-01-15" --devices 50
"""

import os
import sys
import json
import base64
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
KEYS_DIR = BACKEND_DIR / "keys"
OUTPUT_DIR = BACKEND_DIR / "licenses"

PRIVATE_KEY_FILE = KEYS_DIR / ".private"
PUBLIC_KEY_FILE = KEYS_DIR / ".public"


def ensure_dirs():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_keypair() -> bool:
    """生成 RSA-2048 密钥对，仅执行一次"""
    if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():
        return True

    print("[INFO] 首次运行，正在生成 RSA-2048 密钥对...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # 私钥（PKCS#8，您务必保管好，切勿泄露）
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    PRIVATE_KEY_FILE.write_bytes(private_pem)

    # 公钥（随软件交付给学校）
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    PUBLIC_KEY_FILE.write_bytes(public_pem)

    print(f"[OK] 私钥已保存: {PRIVATE_KEY_FILE}")
    print(f"[OK] 公钥已保存: {PUBLIC_KEY_FILE}")
    print("[WARN] 请妥善保管私钥文件，丢失后将无法生成新的授权文件！")
    return True


def load_private_key():
    """加载私钥"""
    pem = PRIVATE_KEY_FILE.read_bytes()
    return serialization.load_pem_private_key(pem, password=None, backend=default_backend())


def create_license(school: str, expire_ts: int, max_devices: int) -> dict:
    """构建授权内容并签名"""
    content = {
        "n": school,           # name
        "u": expire_ts,        # until (timestamp)
        "d": max_devices,      # max devices
        "i": int(datetime.utcnow().timestamp()),  # issued at
        "v": 1,                # version
    }

    content_json = json.dumps(content, separators=(",", ":"), ensure_ascii=False)
    content_b64 = base64.b64encode(content_json.encode("utf-8")).decode("utf-8")

    private_key = load_private_key()
    signature = private_key.sign(
        content_b64.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    signature_b64 = base64.b64encode(signature).decode("utf-8")

    return {
        "c": content_b64,      # content
        "s": signature_b64,    # signature
    }


def main():
    parser = argparse.ArgumentParser(
        description="为 IoTPlatform 生成学校授权文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --school "某某职业技术学院" --months 6 --devices 100
  %(prog)s --school "XX大学" --date 2027-01-15 --devices 50
  %(prog)s --school "测试学校" --days 14 --devices 10
        """
    )
    parser.add_argument("--school", required=True, help="学校名称")
    parser.add_argument("--months", type=int, default=0, help="授权时长（月）")
    parser.add_argument("--days", type=int, default=0, help="授权时长（天）")
    parser.add_argument("--date", help="过期日期（YYYY-MM-DD），优先级高于 months/days")
    parser.add_argument("--devices", type=int, default=100, help="允许接入的最大设备数量")
    parser.add_argument("--out", help="输出文件名（默认自动生成）")

    args = parser.parse_args()

    ensure_dirs()
    generate_keypair()

    # 计算过期时间
    now = datetime.utcnow()
    if args.date:
        try:
            expire = datetime.strptime(args.date, "%Y-%m-%d")
            expire = expire.replace(hour=23, minute=59, second=59)
        except ValueError:
            print("[ERROR] 日期格式错误，请使用 YYYY-MM-DD")
            sys.exit(1)
    elif args.months > 0:
        expire = now + timedelta(days=args.months * 30)
    elif args.days > 0:
        expire = now + timedelta(days=args.days)
    else:
        print("[ERROR] 请指定过期时间：--date、--months 或 --days")
        sys.exit(1)

    expire_ts = int(expire.timestamp())

    # 生成授权
    license_data = create_license(args.school, expire_ts, args.devices)

    # 输出文件
    safe_name = args.school.replace(" ", "_").replace("/", "_")
    default_name = f"{safe_name}_{expire.strftime('%Y%m%d')}.policy"
    out_file = OUTPUT_DIR / (args.out or default_name)
    out_file.write_text(json.dumps(license_data, indent=2), encoding="utf-8")

    # 同时准备部署包说明
    deploy_public = OUTPUT_DIR / f"{safe_name}_deploy_public.key"
    deploy_public.write_bytes(PUBLIC_KEY_FILE.read_bytes())

    print("\n" + "=" * 60)
    print("授权文件生成成功")
    print("=" * 60)
    print(f"学校名称: {args.school}")
    print(f"过期时间: {expire.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"设备上限: {args.devices}")
    print(f"\n授权文件: {out_file}")
    print(f"公钥文件: {deploy_public}")
    print("\n部署说明:")
    print(f"  1. 将 {out_file.name} 重命名为 .policy，放到学校服务器的 backend/ 目录下")
    print(f"  2. 将 {deploy_public.name} 重命名为 .auth，放到学校服务器的 backend/ 目录下")
    print(f"  3. 重启后端服务即可生效")
    print("=" * 60)


if __name__ == "__main__":
    main()
